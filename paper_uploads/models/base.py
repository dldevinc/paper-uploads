import posixpath
from typing import Dict, Type, Any, Optional
from django.apps import apps
from django.db import models
from django.core.files import File
from django.utils.timezone import now
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _
from ..logging import logger
from .containers import ContainerMixinBase


class Permissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('upload', 'Can upload files'),
            ('change', 'Can change files'),
            ('delete', 'Can delete files'),
        )


class UploadedFileBase(ContainerMixinBase, models.Model):
    file = models.CharField(_('file'), max_length=255)  # Example field. Should be overriden
    name = models.CharField(_('file name'), max_length=255, editable=False)
    extension = models.CharField(_('file extension'), max_length=32, editable=False, help_text=_('Lowercase, without leading dot'))
    size = models.PositiveIntegerField(_('file size'), default=0, editable=False)
    hash = models.CharField(_('file hash'), max_length=40, editable=False,
        help_text=_('SHA-1 hash of the file contents')
    )
    created_at = models.DateTimeField(_('created at'), default=now, editable=False)
    uploaded_at = models.DateTimeField(_('uploaded at'), default=now, editable=False)
    modified_at = models.DateTimeField(_('changed at'), auto_now=True, editable=False)

    class Meta:
        abstract = True
        default_permissions = ()

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            self.name
        )

    def save(self, *args, **kwargs):
        is_new_file = False
        if self.file:
            if not self.pk:
                is_new_file = True
            else:
                original = type(self)._base_manager.filter(pk=self.pk).only('file').get()
                is_new_file = original.file != self.file

        super().save(*args, **kwargs)
        if is_new_file:
            # при использовании удаленных storage (типа DropBox), возникает
            # исключение "cannot reopen file", т.к. метод open() объекта
            # DropBoxFile ищет файл на локальном диске.
            self.refresh_from_db()
            self.post_save_new_file()

    @property
    def canonical_name(self) -> str:
        """
        Имя реального файла без учета суффикса, добавляемого FileStorage.
        """
        return '{}.{}'.format(self.name, self.extension)

    def attach_file(self, file: File, **options):
        # skip suffix
        basename = posixpath.basename(file.name)
        file_name, file_ext = posixpath.splitext(basename)
        if not self.name:
            self.name = file_name
        super().attach_file(file, **options)

    def _post_attach_file(self, data=None):
        super()._post_attach_file(data)
        basename = posixpath.basename(self.get_file_name())
        _, file_ext = posixpath.splitext(basename)
        if not self.extension:
            self.extension = file_ext.lstrip('.').lower()
        self.size = self.get_file_size()

        if self.hash:   # перезапись существующего файла
            self.modified_at = now()

        # обновляем дату загрузки
        self.hash = self.get_file_hash()
        self.uploaded_at = now()

    def post_save_new_file(self):
        """
        Метод выполняется после сохранения модели, когда задан новый файл.
        """
        pass

    def as_dict(self) -> Dict[str, Any]:
        """
        Словарь, возвращаемый в виде JSON после загрузки файла.
        Служит для формирования виджета файла без перезагрузки страницы.
        """
        return {
            'id': self.pk,
            'name': self.name,
            'ext': self.extension,
            'size': self.size,
            'url': self.get_file_url(),
        }


class SlaveModelMixin(models.Model):
    """
    Миксина, позволяющая обратиться к модели или полю модели, для которой
    был создан объект.
    """
    owner_app_label = models.CharField(max_length=100, editable=False)
    owner_model_name = models.CharField(max_length=100, editable=False)
    owner_fieldname = models.CharField(max_length=255, editable=False)

    class Meta:
        abstract = True

    def get_owner_model(self) -> Optional[Type[models.Model]]:
        if not self.owner_app_label or not self.owner_model_name:
            return

        try:
            return apps.get_model(self.owner_app_label, self.owner_model_name)
        except LookupError:
            logger.debug("Not found model: %s.%s" % (self.owner_app_label, self.owner_model_name))

    def get_owner_field(self) -> Optional[models.Field]:
        owner_model = self.get_owner_model()
        if owner_model is None:
            return

        try:
            return owner_model._meta.get_field(self.owner_fieldname)
        except FieldDoesNotExist:
            logger.debug(
                "Not found field '%s' in model %s.%s" % (
                    self.owner_app_label, self.owner_model_name, self.owner_fieldname
                )
            )

    @classmethod
    def get_validation(cls) -> Dict[str, Any]:
        """
        Возвращает конфигурацию валидации загружаемых файлов FineUploader.
        https://docs.fineuploader.com/branch/master/api/options.html#validation
        """
        return {}
