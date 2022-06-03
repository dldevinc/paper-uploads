import datetime
import decimal
import io
import os
import pathlib
import posixpath
import warnings
from functools import partial
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple, Union
from xml.dom.minidom import parse

from django.core.exceptions import SuspiciousFileOperation
from django.core.files import File
from django.core.files.storage import FileSystemStorage, Storage
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.fields.files import FieldFile
from django.db.models.utils import make_model_tuple
from django.utils.functional import SimpleLazyObject
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from PIL import Image
from pyexpat import ExpatError
from variations.typing import Size
from variations.utils import prepare_image, replace_extension

from .. import exceptions, helpers, signals
from ..conf import settings
from ..files import VariationFile
from ..typing import FileLike
from ..utils import cached_method, checksum
from ..variations import PaperVariation
from .mixins import FileFieldProxyMixin, FileProxyMixin

try:
    from django.core.files.utils import validate_file_name
except ImportError:
    # new in Django 3.1.10
    def validate_file_name(name, allow_relative_path=False):
        if os.path.basename(name) in {'', '.', '..'}:
            raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)

        if allow_relative_path:
            # Use PurePosixPath() because this branch is checked only in
            # FileField.generate_filename() where all file paths are expected to be
            # Unix style (with forward slashes).
            path = pathlib.PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts:
                raise SuspiciousFileOperation(
                    "Detected path traversal attempt in '%s'" % name
                )
        elif name != os.path.basename(name):
            raise SuspiciousFileOperation("File name '%s' includes path elements" % name)
        return name

__all__ = [
    "NoPermissionsMetaBase",
    "ResourceBaseMeta",
    "Resource",
    "FileResource",
    "FileFieldResource",
    "SVGFileResourceMixin",
    "ImageFileResourceMixin",
    "VariationFile",
    "VersatileImageResourceMixin",
]


class Permissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("upload", "Can upload files"),
            ("change", "Can change files"),
            ("delete", "Can delete files"),
        )


class NoPermissionsMetaBase:
    """
    Отменяет создание автоматических объектов Permission у наследников класса.
    """
    def __new__(cls, name, bases, attrs, **kwargs):
        meta = attrs.pop("Meta", None)
        if meta is None:
            meta = type("Meta", (), {"default_permissions": ()})
        else:
            meta_attrs = meta.__dict__.copy()
            meta_attrs.setdefault("default_permissions", ())
            meta = type("Meta", meta.__bases__, meta_attrs)
        attrs["Meta"] = meta

        return super().__new__(cls, name, bases, attrs, **kwargs)


class ResourceBaseMeta(NoPermissionsMetaBase, models.base.ModelBase):
    """
    Приём, позволяющий переопределить OneToOne-связь между моделями при наследовании
    от абстрактной модели.

    По умолчанию, при наследовании от абстрактной модели, унаследованной от конкретной
    (concrete), попытка переопределния OneToOne-связи не замещает поле по умолчанию,
    а добавляет второе.

    Ссылка:
    https://docs.djangoproject.com/en/3.2/topics/db/models/#specifying-the-parent-link-field
    """

    def __new__(mcs, name, bases, attrs, **kwargs):
        parents = [b for b in bases if isinstance(b, ModelBase)]

        parent_links = {}
        for base in reversed(parents):
            # Conceptually equivalent to `if base is Model`.
            if not hasattr(base, "_meta"):
                continue

            # Locate OneToOneField instances.
            for field in base._meta.local_fields:
                if isinstance(field, models.OneToOneField) and field.remote_field.parent_link:
                    key = make_model_tuple(field.remote_field.model)
                    parent_links.setdefault(key, []).append(field)

        for fieldname, field in list(attrs.items()):
            if isinstance(field, models.OneToOneField) and field.remote_field.parent_link:
                key = make_model_tuple(field.remote_field.model)
                if key in parent_links:
                    inherited_field = parent_links[key].pop()
                    if fieldname != inherited_field.name:
                        # force delete inherited field
                        attrs[inherited_field.name] = None

        return super().__new__(mcs, name, bases, attrs)


class ResourceBase(models.Model, metaclass=ResourceBaseMeta):
    """
    Базовый класс ресурса.
    """
    created_at = models.DateTimeField(
        _("created at"),
        default=now,
        editable=False
    )
    modified_at = models.DateTimeField(
        _("changed at"),
        auto_now=True,
        editable=False
    )

    class Meta:
        abstract = True

    def __repr__(self):
        return "{} #{}".format(type(self).__name__, self.pk)

    def as_dict(self) -> Dict[str, Any]:
        """
        Представление объекта в виде словаря, конвертируемого в JSON.
        Служит для формирования виджета файла без перезагрузки страницы.
        """
        return {
            "id": self.pk,
            "created": self.created_at.isoformat() if self.created_at else None,
            "modified": self.modified_at.isoformat() if self.modified_at else None,
        }


class Resource(ResourceBase):
    """
    Ресурс.

    TODO: после переноса миксины BacklinkModelMixin класс остался пустым.
    """

    class Meta(ResourceBase.Meta):
        abstract = True


class FileResource(FileProxyMixin, Resource):
    """
    Подкласс ресурса, представляющего файл.
    """

    resource_name = models.CharField(
        _("resource name"),
        max_length=255,
        editable=False,
        help_text=_("Human-readable resource name"),
    )
    extension = models.CharField(
        _("extension"),
        max_length=32,
        editable=False,
        help_text=_("Lowercase, without leading dot"),
    )
    size = models.PositiveIntegerField(
        _("size"),
        default=0,
        editable=False
    )
    checksum = models.CharField(
        _("checksum"),
        max_length=64,
        editable=False,
    )
    uploaded_at = models.DateTimeField(
        _("uploaded at"),
        default=now,
        editable=False
    )

    class Meta(Resource.Meta):
        abstract = True

    def __str__(self):
        return self.get_caption()

    def __repr__(self):
        return "{}('{}')".format(type(self).__name__, self.name)

    @property
    def basename(self):
        warnings.warn(
            "'basename' is deprecated in favor of 'resource_name'",
            DeprecationWarning,
            stacklevel=2
        )
        return self.resource_name

    @basename.setter
    def basename(self, value):
        warnings.warn(
            "'basename' is deprecated in favor of 'resource_name'",
            DeprecationWarning,
            stacklevel=2
        )
        self.resource_name = value

    @property
    def name(self) -> str:
        """
        Полное имя загруженного файла.
        Это имя включает относительный путь, суффикс и расширение.
        """
        raise NotImplementedError

    def get_caption(self) -> str:
        """
        Человекопонятное имя файла.
        Не содержит суффикса, которое может быть добавлено файловым хранилищем.
        """
        if self.extension:
            return "{}.{}".format(self.resource_name, self.extension)
        return self.resource_name

    def get_file_size(self) -> int:
        """
        Получение размера загруженного файла.
        """
        raise NotImplementedError

    def file_exists(self) -> bool:
        """
        Проверка существования файла.
        """
        raise NotImplementedError

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.resource_name,
            "extension": self.extension,
            "caption": self.get_caption(),
            "size": self.size,
            "uploaded": self.uploaded_at.isoformat() if self.uploaded_at else None
        }

    def update_checksum(self, file: FileLike = None) -> bool:
        file = file or self.get_file()
        old_checksum = self.checksum
        new_checksum = checksum(file)
        if new_checksum and new_checksum != old_checksum:
            signals.checksum_update.send(
                sender=type(self),
                instance=self,
                checksum=new_checksum
            )
            self.checksum = new_checksum
        return old_checksum != new_checksum

    def attach(self, file: Union[str, Path, FileLike], name: str = None, **options):
        """
        Присоединение файла к экземпляру ресурса.
        Этот метод является обёрткой. Фактическое сохранение файла
        происходит в методе `_attach()`.

        Если на данном этапе обнаруживается, что переданный файл не может
        быть представлен этой моделью, необходимо вызвать исключение
        UnsupportedResource.
        """
        if not name:
            if isinstance(file, str):
                name = file
            elif isinstance(file, Path):
                name = str(file)
            else:
                name = getattr(file, "name", None)

        # prevent path traversal
        if name:
            name = os.path.basename(name)

        # convert to `django.core.files.File` instance
        need_to_close = False
        if isinstance(file, (str, Path)):
            need_to_close = True
            file = File(open(file, "rb"), name=name)
        elif isinstance(file, File):
            file.name = name
        else:
            file = File(file, name=name)

        # reset file position before prepare
        if file.seekable():
            file.seek(0)

        prepared_file = self._prepare_file(file, **options)

        signals.pre_attach_file.send(
            sender=type(self), instance=self, file=prepared_file, options=options
        )

        # reset file position before upload
        if prepared_file.seekable():
            prepared_file.seek(0)

        attach_result = self._attach(prepared_file, **options)

        self.size = self.get_file_size()
        self.uploaded_at = now()
        self.modified_at = now()

        # Рассчет хэша от входного файла, а не от загруженного,
        # т.к. в случае Cloudinary, это приведет к избыточному
        # скачиванию файла из облачного хранилища.
        if prepared_file.seekable():
            prepared_file.seek(0)
            self.update_checksum(prepared_file)
        else:
            self.update_checksum()

        signals.post_attach_file.send(
            sender=type(self),
            instance=self,
            file=self.get_file(),
            options=options,
            response=attach_result,
        )

        if need_to_close:
            if not file.closed:
                file.close()

    def attach_file(self, *args, **kwargs):
        warnings.warn(
            "attach_file() is deprecated in favor of attach()",
            DeprecationWarning,
            stacklevel=2
        )
        return self.attach(*args, **kwargs)

    def _prepare_file(self, file: File, **options) -> File:
        """
        Подготовка файла к присоединению к модели.
        """
        return file

    def _attach(self, file: File, **options):
        raise NotImplementedError

    def _attach_file(self, *args, **kwargs):
        warnings.warn(
            "_attach_file() is deprecated in favor of _attach()",
            DeprecationWarning,
            stacklevel=2
        )
        return self._attach(*args, **kwargs)

    def rename(self, new_name: str, **options):
        """
        Переименование файла.
        Этот метод является обёрткой. Фактическое переименование файла
        происходит в методе `_rename()`.
        """
        self._require_file()

        if not self.file_exists():
            raise FileNotFoundError(self.name)

        old_name = self.name

        signals.pre_rename_file.send(
            sender=type(self),
            instance=self,
            old_name=old_name,
            new_name=new_name,
            options=options,
        )

        response = self._rename(new_name, **options)

        self.modified_at = now()

        signals.post_rename_file.send(
            sender=type(self),
            instance=self,
            old_name=old_name,
            new_name=new_name,
            options=options,
            response=response,
        )

    def rename_file(self, *args, **kwargs):
        warnings.warn(
            "rename_file() is deprecated in favor of rename()",
            DeprecationWarning,
            stacklevel=2
        )
        return self.rename(*args, **kwargs)

    def _rename(self, new_name: str, **options):
        raise NotImplementedError

    def _rename_file(self, *args, **kwargs):
        warnings.warn(
            "_rename_file() is deprecated in favor of _rename()",
            DeprecationWarning,
            stacklevel=2
        )
        return self._rename(*args, **kwargs)

    def delete_file(self, **options):
        """
        Удаление файла.
        Этот метод является обёрткой. Фактическое удаление файла
        происходит в методе `_delete_file()`.
        """
        signals.pre_delete_file.send(sender=type(self), instance=self, options=options)
        response = self._delete_file(**options)
        signals.post_delete_file.send(sender=type(self), instance=self, options=options, response=response)

    def _delete_file(self, **options):
        raise NotImplementedError


class FileFieldResource(FileFieldProxyMixin, FileResource):
    """
    Подкласс файлового ресурса, доступ к которому осуществляется через Django Storage.
    """

    class Meta(FileResource.Meta):
        abstract = True

    def _require_file(self):
        file = self.get_file()
        if not file:
            file_field = self.get_file_field()
            raise ValueError(_("The '%s' attribute has no file associated with it.") % file_field.name)

    def _attach(self, file: File, **options):
        self.get_file().save(file.name, file, save=False)
        self.resource_name = helpers.get_filename(file.name)
        self.extension = helpers.get_extension(self.name)

    def _rename(self, new_name: str, **options):
        # копирование файла, чтобы не вредить кэшированию
        file = self.get_file()
        with file.open() as fp:
            file.save(new_name, fp, save=False)

        self.resource_name = helpers.get_filename(new_name)
        self.extension = helpers.get_extension(self.name)

    def _delete_file(self, **options):
        self.get_file().delete(save=False)

    @property
    def name(self) -> str:
        self._require_file()
        return self.get_file().name

    @classmethod
    def get_file_field(cls):
        """
        Получение файлового поля модели.
        """
        raise NotImplementedError

    def get_file_folder(self) -> str:
        """
        Возвращает путь к папке, в которую будет сохранен файл.
        """
        raise NotImplementedError

    def get_file_storage(self) -> Storage:
        raise NotImplementedError

    def generate_filename(self, filename: str) -> str:
        """
        Формирование каталога и имени файла при сохранении.
        """
        dirname = self.get_file_folder()
        dirname = datetime.datetime.now().strftime(dirname)
        filename = posixpath.join(dirname, filename)
        filename = validate_file_name(filename, allow_relative_path=True)

        storage = self.get_file_storage()
        return storage.generate_filename(filename)

    def get_file(self) -> FieldFile:
        raise NotImplementedError

    def set_file(self, value):
        field = self.get_file_field()
        setattr(self, field.attname, value)

    def get_file_size(self) -> int:
        self._require_file()
        return self.get_file().size

    def get_file_url(self) -> str:
        warnings.warn(
            "get_file_url() is deprecated in favor of 'url' property",
            DeprecationWarning,
            stacklevel=2
        )
        return self.url

    def file_exists(self) -> bool:
        file = self.get_file()
        if not file:
            return False
        return file.storage.exists(file.name)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "url": self.url,
        }


class SVGFileResourceMixin(models.Model):
    """
    Подкласс файлового ресурса для SVG-изображений.
    """

    title = models.CharField(
        _("title"),
        max_length=255,
        blank=True,
        help_text=_(
            "The title is being used as a tooltip when the user hovers the mouse over the image"
        ),
    )
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_(
            "This text will be used by screen readers, search engines, or when the image cannot be loaded"
        ),
    )
    width = models.DecimalField(
        _("width"),
        max_digits=10,
        decimal_places=4,
        default=0,
        editable=False
    )
    height = models.DecimalField(
        _("height"),
        max_digits=10,
        decimal_places=4,
        default=0,
        editable=False
    )

    class Meta:
        abstract = True

    @property
    def width_display(self):
        width = str(self.width)
        return width.rstrip("0").rstrip(".") if "." in width else width

    @property
    def height_display(self):
        height = str(self.height)
        return height.rstrip("0").rstrip(".") if "." in height else height

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),  # noqa
            "width": self.width_display,
            "height": self.height_display,
            "title": self.title,
            "description": self.description,
        }

    def _prepare_file(self, file: File, **options) -> File:
        try:
            dom = parse(file)
        except ExpatError:
            raise exceptions.UnsupportedResource(
                _("File `%s` is not an svg image") % file.name
            )

        root = dom.documentElement
        if root.tagName.lower() != "svg":
            raise exceptions.UnsupportedResource(
                _("File `%s` is not an svg image") % file.name
            )

        width = root.getAttribute("width")
        height = root.getAttribute("height")
        view_box = root.getAttribute("viewBox")
        view_box = view_box.split(" ") if view_box else []

        if not width and len(view_box) == 4:
            width = view_box[2]

        if not height and len(view_box) == 4:
            height = view_box[3]

        try:
            self.width = round(decimal.Decimal(width), 4)
        except decimal.InvalidOperation:
            self.width = 0

        try:
            self.height = round(decimal.Decimal(height), 4)
        except decimal.InvalidOperation:
            self.height = 0

        return super()._prepare_file(file, **options)  # noqa: F821


class ImageFileResourceMixin(models.Model):
    """
    Подкласс файлового ресурса для изображений
    """

    title = models.CharField(
        _("title"),
        max_length=255,
        blank=True,
        help_text=_(
            "The title is being used as a tooltip when the user hovers the mouse over the image"
        ),
    )
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_(
            "This text will be used by screen readers, search engines, or when the image cannot be loaded"
        ),
    )
    width = models.PositiveSmallIntegerField(
        _("width"),
        default=0,
        editable=False
    )
    height = models.PositiveSmallIntegerField(
        _("height"),
        default=0,
        editable=False
    )
    cropregion = models.CharField(
        _("crop region"),
        max_length=24,
        blank=True,
        editable=False
    )

    class Meta:
        abstract = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),  # noqa
            "width": self.width,
            "height": self.height,
            "cropregion": self.cropregion,
            "title": self.title,
            "description": self.description,
        }

    def _prepare_file(self, file: File, **options) -> File:
        try:
            image = Image.open(file)
        except OSError:
            raise exceptions.UnsupportedResource(
                _("File `%s` is not an image") % file.name
            )
        else:
            self.width, self.height = image.size

            # format extension
            file.name = replace_extension(file.name, format=image.format)
            root, ext = os.path.splitext(file.name)
            ext = ext.lstrip(".").lower()
            file.name = ".".join([root, ext])

        return super()._prepare_file(file, **options)  # noqa: F821


class VersatileImageResourceMixin(ImageFileResourceMixin):
    """
    Подкласс файлового ресурса для вариативного изображения.
    """

    # класс файла вариации
    variation_class = VariationFile

    # флаг, запускающий нарезку вариаций после сохранения экземпляра модели в БД
    need_recut = False

    class Meta(ImageFileResourceMixin.Meta):
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reset_variation_files()

    def __getattr__(self, item):
        # реализация-заглушка, чтобы PyCharm не ругался на атрибуты-вариации
        raise AttributeError(
            "{!r} object has no attribute {!r}".format(self.__class__.__name__, item)
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.need_recut:
            self.need_recut = False
            if settings.RQ_ENABLED:
                self.recut_async()
            else:
                self.recut()

    def _reset_variation_files(self):
        """
        Обновление файлов вариаций в текущем экземпляре.
        """

        # Очистка кэша метода variation_files()
        if hasattr(self, self.variation_files.cache_key):
            delattr(self, self.variation_files.cache_key)

        try:
            for vname in self.get_variations():
                self.__dict__[vname] = SimpleLazyObject(partial(self.get_variation_file, vname))
        except exceptions.CollectionModelNotFoundError:
            pass

    @cached_method("_variation_files_cache")
    def variation_files(self) -> Tuple[Tuple[str, VariationFile]]:
        if not self.get_file():
            raise cached_method.Bypass(tuple())

        return tuple(
            (vname, self.get_variation_file(vname))
            for vname in self.get_variations()
        )

    def get_variation_file(self, variation_name: str) -> VariationFile:
        return self.variation_class(instance=self, variation_name=variation_name)

    def get_variations(self) -> Dict[str, PaperVariation]:
        raise NotImplementedError

    def attach(self, file: FileLike, name: str = None, **options):
        super().attach(file, name=name, **options)  # noqa: F821
        self.need_recut = True
        self._reset_variation_files()

    def rename(self, new_name: str, **options):
        super().rename(new_name, **options)  # noqa: F821
        self.need_recut = True
        self._reset_variation_files()

    def delete_file(self, **options):
        super().delete_file(**options)  # noqa: F821
        self.delete_variations()

    def delete_variations(self):
        for vname, vfile in self.variation_files():
            vfile.delete()

        self._reset_variation_files()

    def recut(self, names: Iterable[str] = ()):
        """
        Нарезка вариаций.
        Можно указать имена конкретных вариаций в параметре `names`.
        """
        if not self.file_exists():
            raise FileNotFoundError(self.name)

        file = self.get_file()
        with file.open() as source:
            img = Image.open(source)
            draft_size = self.calculate_max_size(img.size)
            img = prepare_image(img, draft_size=draft_size)

            for vname, variation in self.get_variations().items():
                if names and vname not in names:
                    continue

                image = variation.process(img)
                self._save_variation(vname, variation, image)

                signals.variation_created.send(
                    sender=type(self),
                    instance=self,
                    name=vname
                )

    def calculate_max_size(self, source_size: Size) -> Optional[Tuple[int, int]]:
        """
        Вычисление максимально возможных значений ширины и высоты изображения
        среди всех вариаций, чтобы передать их в Image.draft().
        """
        max_width = 0
        max_height = 0
        for name, variation in self.get_variations().items():
            size = variation.get_output_size(source_size)
            max_width = max(max_width, size[0])
            max_height = max(max_height, size[1])
        if max_width and max_height:
            return max_width, max_height

    def _save_variation(self, name: str, variation: PaperVariation, image: Image):
        """
        Запись изображения в файловое хранилище
        """
        variation_file = self.get_variation_file(name)

        if isinstance(variation_file.storage, FileSystemStorage):
            with variation_file.open("wb") as fp:
                variation.save(image, fp)
        else:
            # Не все Storage-классы позволяют записывать контент с помощью вызовов
            # `open()` и `write()`. Для них нужно использовать метод `_save()`.
            with io.BytesIO() as buffer:
                variation.save(image, buffer)
                content = File(buffer, name=variation_file.name)
                variation_file.storage._save(variation_file.name, content)

    def recut_async(self, names: Iterable[str] = ()):
        """
        Добавление задачи нарезки вариаций в django-rq.
        """
        from django_rq.queues import get_queue

        queue = get_queue(settings.RQ_QUEUE_NAME)
        queue.enqueue_call(
            self._recut_task,
            kwargs={
                "app_label": self._meta.app_label,
                "model_name": self._meta.model_name,
                "object_id": self.pk,
                "using": self._state.db,
                "names": names,
            },
        )

    @classmethod
    def _recut_task(
        cls,
        app_label: str,
        model_name: str,
        object_id: int,
        using: str,
        names: Iterable[str],
    ):
        """
        Задача для django-rq.
        Вызывает `recut()` экземпляра в отдельном процессе.
        """
        instance = helpers.get_instance(app_label, model_name, object_id, using=using)
        instance.recut(names)
