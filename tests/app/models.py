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
from paper_uploads.variations import PaperVariation


class DummyResource(Resource):
    pass


class DummyFileResource(FileResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__name = 'File_ABCD.jpg'

    def get_file(self) -> File:
        buffer = io.BytesIO()
        buffer.write(b'This is example file content')
        buffer.seek(0)
        return File(buffer, name=self.name)

    def get_file_name(self) -> str:
        return self.__name

    def get_file_url(self):
        return 'http://example.com/{}'.format(quote(self.get_basename()))

    def file_exists(self) -> bool:
        return True

    def _attach_file(self, file: File, **options):
        return {
            'success': True,
        }

    def _rename_file(self, new_name: str, **options):
        self.__name = new_name
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
        # just for the test VariationFile with non-versatile resource
        return {
            'desktop': PaperVariation(
                name='desktop',
                size=(800, 0),
                clip=False
            ),
        }


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


class DummyBacklinkResource(BacklinkModelMixin, FileFieldResource):
    file = models.FileField(_('file'), upload_to='reverse_file')

    def get_file(self) -> FieldFile:
        return self.file


class DummyReadonlyFileProxyResource(ReadonlyFileProxyMixin, FileFieldResource):
    file = models.FileField(_('file'), upload_to='readonly_file')

    def get_file(self) -> FieldFile:
        return self.file


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


class Page(models.Model):
    header = models.CharField(_('header'), max_length=255)
    file = FileField(_('simple file'), blank=True)
    # image = ImageField(_('simple image'), blank=True)

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def __str__(self):
        return self.header


class Document(models.Model):
    page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(_('title'), max_length=255)
    file = FileField(_('simple file'), blank=True)
    # image = ImageField(_('simple image'), blank=True)

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
