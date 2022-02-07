import io
from typing import Dict
from urllib.parse import quote

from django.core.files import File
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from paper_uploads import helpers
from paper_uploads.helpers import build_variations
from paper_uploads.models.base import *
from paper_uploads.models.mixins import BacklinkModelMixin
from paper_uploads.variations import PaperVariation

__all__ = [
    "DummyResource",
    "DummyBacklinkResource",
    "DummyFileResource",
    "DummyFileFieldResource",
    "DummyImageFieldResource",
    "DummyVersatileImageResource",
]


class DummyResource(Resource):
    pass


class DummyBacklinkResource(BacklinkModelMixin, Resource):
    pass


class DummyFileResource(FileResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__filename = '{}.{}'.format(self.basename, self.extension)

    def get_file(self) -> File:
        file = getattr(self, '_file_cache', None)
        if file is None:
            buffer = io.BytesIO()
            buffer.write(b'This is example file content')
            buffer.seek(0)
            file = self._file_cache = File(buffer, name=self.basename)
        return file

    @property
    def name(self) -> str:
        return self.__filename

    def get_file_field(self) -> models.FileField:
        return models.Field(name='file')

    def get_file_size(self) -> int:
        return 28

    def get_file_url(self):
        return 'http://example.com/{}'.format(quote(self.get_caption()))

    def file_exists(self) -> bool:
        return True

    def _attach(self, file: File, **options):
        self.__filename = file.name
        self.basename = helpers.get_filename(file.name)
        self.extension = helpers.get_extension(file.name)
        return {
            'success': True,
        }

    def _rename(self, new_name: str, **options):
        self.__filename = new_name
        self.basename = helpers.get_filename(new_name)
        self.extension = helpers.get_extension(new_name)
        return {
            'success': True,
        }

    def _delete_file(self, **options):
        return {
            'success': True,
        }


class DummyFileFieldResource(FileFieldResource):
    file = models.FileField(_("file"), upload_to="file_field")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__name = "File_ABCD.jpg"

    def get_file(self) -> FieldFile:
        return self.file

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("file")


class DummyImageFieldResource(ImageFileResourceMixin, FileFieldResource):
    image = models.FileField(_("file"), upload_to="image_field")

    def get_file(self) -> FieldFile:
        return self.image

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("image")

    def get_variations(self) -> Dict[str, PaperVariation]:
        variations = getattr(self, "_variations", None)
        if variations is None:
            variations = self._variations = {
                "desktop": PaperVariation(
                    name="desktop",
                    size=(800, 0),
                    clip=False
                ),
            }
        return variations


class DummyVersatileImageResource(VersatileImageResourceMixin, FileFieldResource):
    file = models.FileField(_("file"), upload_to="versatile_image")

    def get_file(self) -> FieldFile:
        return self.file

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("file")

    def get_variations(self) -> Dict[str, PaperVariation]:
        return build_variations({
            "desktop": dict(
                size=(800, 0),
                clip=False
            ),
            "mobile": dict(
                size=(0, 600),
                clip=False
            ),
            "micro": dict(
                name="square",
                size=(200, 200),
            ),
        })
