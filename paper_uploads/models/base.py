import hashlib
import posixpath
from typing import Dict, Type, Any, Optional
from itertools import chain
from django.apps import apps
from django.db import models
from django.core import checks
from django.utils.timezone import now
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _
from ..storage import upload_storage
from ..conf import PROXY_FILE_ATTRIBUTES
from ..logging import logger


class Permissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('upload', 'Can upload files'),
            ('change', 'Can change files'),
            ('delete', 'Can delete files'),
        )


class UploadedFileBase(models.Model):
    file = models.FileField(_('file'), max_length=255, storage=upload_storage)  # Example field. Should be overriden
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
            self.file.path
        )

    def __getattr__(self, item):
        # для вызова через super() в классах-потомках
        raise AttributeError(
            "'%s' object has no attribute '%s'" % (self.__class__.__name__, item)
        )

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_prohibited_field_names(),
        ]

    @classmethod
    def _check_prohibited_field_names(cls, **kwargs):
        errors = []
        for field in chain(cls._meta.local_fields, cls._meta.local_many_to_many):
            if field.name in PROXY_FILE_ATTRIBUTES:
                errors.append(
                    checks.Error(
                        "The field '%s' clashes with the proxied file attribute '%s'" % (
                            field.name, field.name
                        ),
                        obj=cls,
                    )
                )
        return errors

    def save(self, *args, **kwargs):
        is_new_file = False
        if self.file:
            if not self.pk:
                is_new_file = True
            else:
                original = type(self)._base_manager.filter(pk=self.pk).only('file').get()
                is_new_file = original.file != self.file

        if is_new_file:
            self.pre_save_new_file()
        super().save(*args, **kwargs)
        if is_new_file:
            self.post_save_new_file()

    @property
    def canonical_name(self) -> str:
        """
        Имя реального файла без учета суффикса, добавляемого FileStorage.
        """
        return '{}.{}'.format(self.name, self.extension)

    def pre_save_new_file(self):
        """
        Метод выполняется перед сохранением модели, когда задан новый файл.
        """
        basename = posixpath.basename(self.file.name)
        filename, ext = posixpath.splitext(basename)
        if not self.name:
            self.name = filename
        self.extension = ext.lstrip('.').lower()
        self.size = self.file.size

        # обновляем дату загрузки если хэш изменился
        current_hash_value = self.hash
        self.update_hash(commit=False)
        if current_hash_value and current_hash_value != self.hash:
            self.uploaded_at = now()

    def post_save_new_file(self):
        """
        Метод выполняется после сохранения модели, когда задан новый файл.
        """
        pass

    def post_delete_callback(self):
        """
        Метод выполняется после удаления экземпляра модели.
        """
        self.file.delete(save=False)

    def update_hash(self, commit: bool = True):
        # keep file state
        file_closed = self.file.closed
        sha1 = hashlib.sha1()
        for chunk in self.file.open():
            sha1.update(chunk)
        if file_closed:
            self.file.close()
        else:
            self.file.seek(0)

        self.hash = sha1.hexdigest()
        if commit:
            self.save(update_fields=['hash'])

    def as_dict(self) -> Dict[str, Any]:
        """
        Словарь, возвращаемый в виде JSON после загрузки файла.
        Служит для формирования виджета файла без перезагрузки страницы.
        """
        return {
            'instance_id': self.pk,
            'name': self.name,
            'ext': self.extension,
            'size': self.size,
            'url': self.file.url,
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
        см. https://docs.fineuploader.com/branch/master/api/options.html#validation
        """
        return {}


class ProxyFileAttributesMixin:
    FILE_FILED = 'file'

    def __getattr__(self, item):
        """ Перенос часто используемых методов файла на уровень модели """
        if item in PROXY_FILE_ATTRIBUTES:
            file_field = getattr(self, self.FILE_FILED)
            return getattr(file_field, item)
        return super().__getattr__(item)