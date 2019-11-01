from typing import Dict, Any
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from ..conf import settings
from ..storage import upload_storage
from ..postprocess import postprocess_variation
from ..variations import PaperVariation
from .fields import VariationalFileField
from .base import (
    VariationFile, ReverseFieldModelMixin, ReadonlyFileProxyMixin,
    VersatileImageResourceMixin, PostprocessableFileFieldResource
)


class UploadedImage(ReverseFieldModelMixin, ReadonlyFileProxyMixin, VersatileImageResourceMixin, PostprocessableFileFieldResource):
    file = VariationalFileField(_('file'), max_length=255, upload_to=settings.IMAGES_UPLOAD_TO, storage=upload_storage)

    class Meta(PostprocessableFileFieldResource.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def get_file(self) -> FieldFile:
        return self.file

    def postprocess(self, **kwargs):
        # Исходник изображения не обрабатываем
        pass

    def postprocess_variation(self, file: VariationFile, variation: PaperVariation):
        owner_field = self.get_owner_field()
        postprocess_variation(file, variation, field=owner_field)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            'file_info': '({ext}, {width}x{height}, {size})'.format(
                ext=self.extension,
                width=self.width,
                height=self.height,
                size=filesizeformat(self.size)
            )
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
    def get_validation(cls) -> Dict[str, Any]:
        # TODO: магический метод
        return {
            'acceptFiles': ['image/*'],
        }
