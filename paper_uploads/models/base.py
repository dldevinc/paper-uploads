import hashlib
import posixpath
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
    file = models.FileField(_('file'), max_length=255, storage=upload_storage)
    name = models.CharField(_('file name'), max_length=255, blank=True)
    extension = models.CharField(_('file extension'), max_length=32, blank=True)
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
        """ Перенос часто используемых методов файла на уровень модели """
        if item in PROXY_FILE_ATTRIBUTES:
            return getattr(self.file, item)
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
                original = type(self)._meta.base_manager.filter(pk=self.pk).only('file').get()
                is_new_file = original.file != self.file

        if is_new_file:
            self.pre_save_new_file()
        super().save(*args, **kwargs)
        if is_new_file:
            self.post_save_new_file()

    @property
    def canonical_name(self):
        return '{}.{}'.format(self.name, self.extension)

    def pre_save_new_file(self):
        """
        Метод выполняется перед сохранением модели, когда задан новый файл.
        """
        basename = posixpath.basename(self.file.name)
        filename, ext = posixpath.splitext(basename)
        self.name = filename
        self.extension = ext.lower()[1:]
        self.size = self.file.size
        self.update_hash(commit=False)

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

    def update_hash(self, commit=True):
        old_hash = self.hash
        file_closed = self.file.closed
        fp = self.file.open()
        self.hash = hashlib.sha1(fp.read()).hexdigest()
        if file_closed:
            self.file.close()
        else:
            self.file.seek(0)

        # обновляем дату загрузки если хэш изменился
        if old_hash and old_hash != self.hash:
            self.uploaded_at = now()

        if commit:
            self.save(update_fields=['hash'])

    def as_dict(self):
        """
        Словарь, возвращаемый в виде JSON после загрузки файла.

        :return: dict
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

    def get_owner_model(self):
        try:
            return apps.get_model(self.owner_app_label, self.owner_model_name)
        except LookupError:
            logger.debug("Not found model: %s.%s" % (self.owner_app_label, self.owner_model_name))

    def get_owner_field(self):
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
