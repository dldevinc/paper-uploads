import io
from typing import Dict
from urllib.parse import quote

from django.core.files import File
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from paper_uploads.models import *
from paper_uploads.models.base import *
from paper_uploads.typing import *
from paper_uploads.validators import *
from paper_uploads.variations import PaperVariation


class DummyResource(Resource):
    pass


class DummyFileResource(FileResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__filename = '{}.{}'.format(self.name, self.extension)

    def get_file(self) -> File:
        file = getattr(self, '_file', None)
        if file is None:
            buffer = io.BytesIO()
            buffer.write(b'This is example file content')
            buffer.seek(0)
            file = self._file = File(buffer, name=self.name)
        return file

    def get_file_name(self) -> str:
        return '{}'.format(self.__filename)

    def get_file_url(self):
        return 'http://example.com/{}'.format(quote(self.get_basename()))

    def file_exists(self) -> bool:
        return True

    def _attach_file(self, file: File, **options):
        self.__filename = file.name
        return {
            'success': True,
        }

    def _rename_file(self, new_name: str, **options):
        self.__filename = new_name
        return {
            'success': True,
        }

    def _delete_file(self):
        pass


class DummyFileFieldResource(FileFieldResource):
    file = models.FileField(_('file'), upload_to='file_field')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__name = 'File_ABCD.jpg'

    def get_file(self) -> FieldFile:
        return self.file


class DummyImageFieldResource(ImageFileResourceMixin, FileFieldResource):
    image = models.FileField(_('file'), upload_to='image_field')

    def get_file(self) -> FieldFile:
        return self.image

    def get_variations(self) -> Dict[str, PaperVariation]:
        variations = getattr(self, '_variations', None)
        if variations is None:
            variations = self._variations = {
                'desktop': PaperVariation(
                    name='desktop',
                    size=(800, 0),
                    clip=False
                ),
            }
        return variations


class DummyVersatileImageResource(VersatileImageResourceMixin, FileFieldResource):
    file = models.FileField(_('file'), upload_to='versatile_image')

    def get_file(self) -> FieldFile:
        return self.file

    def get_variations(self) -> Dict[str, PaperVariation]:
        return {
            'desktop': PaperVariation(
                name='desktop',
                size=(800, 0),
                clip=False
            ),
            'mobile': PaperVariation(
                name='mobile',
                size=(0, 600),
                clip=False
            ),
        }


class FileExample(models.Model):
    file = FileField(_('file'))


class ImageExample(models.Model):
    image = ImageField(_('image'), variations=dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
    ))


class FileCollection(Collection):
    file = CollectionItem(FileItem)


class PhotoCollection(ImageCollection):
    pass


class IsolatedFileCollection(Collection):
    file = CollectionItem(FileItem)

    class Meta:
        proxy = False


class ChildFileCollection(IsolatedFileCollection):
    file = None
    image = CollectionItem(ImageItem)
    svg = CollectionItem(SVGItem)


class CompleteCollection(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)

    VARIATIONS = dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
    )


# ======================================================================================


class FileFieldObject(models.Model):
    file = FileField(_('file'), blank=True)
    file_required = FileField(_('required file'))

    file_extensions = FileField(
        _('Extension'),
        blank=True,
        validators=[
            ExtensionValidator(['.pdf', '.txt', '.doc'])
        ],
        help_text=_('Only `pdf`, `txt` and `doc` allowed')
    )
    file_mimetypes = FileField(
        _('MimeType'),
        blank=True,
        validators=[
            MimeTypeValidator(['image/svg', 'image/gif'])
        ],
        help_text=_('Only `image/svg` and `image/gif` allowed')
    )
    file_size = FileField(
        _('Size'),
        blank=True,
        validators=[
            SizeValidator('16kb')
        ],
        help_text=_('Maximum file size is 16Kb')
    )

    class Meta:
        verbose_name = _('File')
        verbose_name_plural = _('Files')

    def __str__(self):
        if self.file:
            return self.file.name
        else:
            return 'FileObject'


class ImageFieldObject(models.Model):
    image = ImageField(_('image'), blank=True)
    image_required = ImageField(_('required image'))

    image_extensions = ImageField(
        _('Extension'),
        blank=True,
        validators=[
            ExtensionValidator(['.png', '.gif'])
        ],
        help_text=_('Only `png` and `gif` allowed')
    )
    image_mimetypes = ImageField(
        _('MimeType'),
        blank=True,
        validators=[
            MimeTypeValidator(['image/png', 'image/jpeg'])
        ],
        help_text=_('Only `image/png` and `image/jpeg` allowed')
    )
    image_size = ImageField(
        _('Size'),
        blank=True,
        validators=[
            SizeValidator('64kb')
        ],
        help_text=_('Maximum file size is 64Kb')
    )
    image_min_size = ImageField(
        _('Min size'),
        blank=True,
        validators=[
            ImageMinSizeValidator(640, 480)
        ],
        help_text=_('Image should be at least 640x480 pixels')
    )
    image_max_size = ImageField(
        _('Max size'),
        blank=True,
        validators=[
            ImageMaxSizeValidator(1024, 768)
        ],
        help_text=_('Image should be at most 1024x768 pixels')
    )

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')

    def __str__(self):
        if self.image:
            return self.image.name
        else:
            return 'ImageObject'
