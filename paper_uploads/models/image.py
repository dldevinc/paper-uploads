from typing import Any, Dict

from django.db.models.fields.files import FieldFile
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from ..conf import settings
from ..storage import upload_storage
from ..variations import PaperVariation
from .base import FileFieldResource, VersatileImageResourceMixin
from .fields import VariationalFileField


class UploadedImage(VersatileImageResourceMixin, FileFieldResource):
    file = VariationalFileField(
        _('file'),
        max_length=255,
        upload_to=settings.IMAGES_UPLOAD_TO,
        storage=upload_storage,
    )

    class Meta(FileFieldResource.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def get_file(self) -> FieldFile:
        return self.file

    def set_file(self, value):
        self.file = value

    def get_file_field(self) -> VariationalFileField:
        return self._meta.get_field('file')

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'file_info': '({ext}, {width}x{height}, {size})'.format(
                ext=self.extension,
                width=self.width,
                height=self.height,
                size=filesizeformat(self.size),
            ),
        }

    def get_variations(self) -> Dict[str, PaperVariation]:
        if not hasattr(self, '_variations_cache'):
            owner_field = self.get_owner_field()
            if owner_field is not None:
                self._variations_cache = getattr(owner_field, 'variations', {}).copy()
            else:
                return {}
        return self._variations_cache

    @classmethod
    def get_configuration(cls) -> Dict[str, Any]:
        # TODO: магический метод
        return {
            'image': True,
            'acceptFiles': ['image/*'],
        }
