import os
import shutil
import tempfile
from typing import Dict

from django.core.files import File
from django.core.files.storage import Storage
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from paper_uploads import helpers
from paper_uploads.helpers import build_variations
from paper_uploads.models.base import *
from paper_uploads.models.fields.base import DynamicStorageFileField
from paper_uploads.storage import default_storage
from paper_uploads.variations import PaperVariation

__all__ = [
    "DummyResource",
    "DummyFileResource",
    "DummyFileFieldResource",
    "DummyImageFieldResource",
    "DummyVersatileImageResource",
]


class DummyResource(Resource):
    pass


class DummyFileResource(FileResource):
    """
    Сохраняет файлы в папку /tmp/.
    К имени фала добавляется соль, чтобы при паараллельном запуске
    разные тесты не использовали один файл.
    """
    _name = ""

    @property
    def name(self) -> str:
        return self._name

    def _require_file(self):
        if not self.file_exists():
            raise FileNotFoundError(self.name)

    def get_file(self) -> File:
        return File(None, name=self.name)

    def get_file_size(self) -> int:
        return os.path.getsize(self.name) if self.name else 0

    def file_exists(self) -> bool:
        return os.path.exists(self.name) if self.name else False

    def _attach(self, file: File, **options):
        self.resource_name = helpers.get_filename(file.name)
        self.extension = helpers.get_extension(file.name)

        filename = "{}_{}.{}".format(
            self.resource_name,
            get_random_string(6),
            self.extension
        )

        self._name = os.path.join(
            tempfile.gettempdir(),
            filename
        )
        with open(self._name, "wb") as fdst:
            shutil.copyfileobj(file, fdst)

        return {
            "success": True,
        }

    def _rename(self, new_name: str, **options):
        original_basename = os.path.basename(self.name)
        if original_basename == new_name:
            return {
                "same_name": True
            }

        self.resource_name = helpers.get_filename(new_name)
        self.extension = helpers.get_extension(new_name)

        filename = "{}_{}.{}".format(
            self.resource_name,
            get_random_string(6),
            self.extension
        )
        new_name = os.path.join(
            tempfile.gettempdir(),
            filename
        )
        os.rename(self.name, new_name)
        self._name = new_name

        return {
            "success": True,
        }

    def _delete_file(self, **options):
        os.unlink(self.name)

        return {
            "success": True,
        }


class DummyFileFieldResource(FileFieldResource):
    file = DynamicStorageFileField(_("file"))

    def get_file(self) -> FieldFile:
        return self.file

    @classmethod
    def get_file_field(cls) -> models.FileField:
        return cls._meta.get_field("file")

    def get_file_folder(self) -> str:
        return "file_field"

    def get_file_storage(self) -> Storage:
        return default_storage


class DummyImageFieldResource(ImageFileResourceMixin, FileFieldResource):
    image = DynamicStorageFileField(_("file"))

    def get_file(self) -> FieldFile:
        return self.image

    @classmethod
    def get_file_field(cls) -> models.FileField:
        return cls._meta.get_field("image")

    def get_file_folder(self) -> str:
        return "image_field"

    def get_file_storage(self) -> Storage:
        return default_storage


class DummyVersatileImageResource(VersatileImageResourceMixin, FileFieldResource):
    image = DynamicStorageFileField(_("file"))

    def get_file(self) -> FieldFile:
        return self.image

    @classmethod
    def get_file_field(cls) -> models.FileField:
        return cls._meta.get_field("image")

    def get_file_folder(self) -> str:
        return "versatile_image_field"

    def get_file_storage(self) -> Storage:
        return default_storage

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
