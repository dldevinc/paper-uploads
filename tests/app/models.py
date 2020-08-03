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


class IsolatedFileCollection(Collection):
    file = CollectionItem(FileItem)

    class Meta:
        proxy = False


class ChildFileCollection(IsolatedFileCollection):
    file = None
    image = CollectionItem(ImageItem)
    svg = CollectionItem(SVGItem)


class CompleteCollection(Collection):
    image = CollectionItem(ImageItem)
    svg = CollectionItem(SVGItem)
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

    file_extensions = FileField(_('Extension'), blank=True, validators=[
        ExtensionValidator(['.pdf', '.txt', '.doc'])
    ], help_text=_('Only `pdf`, `txt` and `doc` allowed'))
    file_mimetypes = FileField(_('MimeType'), blank=True, validators=[
        MimeTypeValidator(['image/svg', 'image/gif'])
    ], help_text=_('Only `image/svg` and `image/gif` allowed'))
    file_size = FileField(_('Size'), blank=True, validators=[
        SizeValidator('16kb')
    ], help_text=_('Maximum file size is 16Kb'))
