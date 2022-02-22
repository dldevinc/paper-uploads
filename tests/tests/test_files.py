import os
import shutil

import pytest
from django.conf import settings

from app.models import DummyVersatileImageResource
from paper_uploads.files import VariationFile
from paper_uploads.variations import PaperVariation

from . import utils
from .dummy import *


class TestVariationFile:
    resource_class = DummyVersatileImageResource
    resource_folder = "versatile_image_field"

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        with open(NASA_FILEPATH, "rb") as fp:
            storage.resource.attach(fp)

        assert storage.resource.need_recut is True
        storage.resource.save()

        storage.file = VariationFile(storage.resource, "desktop")

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_name(self, storage):
        assert utils.match_path(
            storage.resource.name,
            "{}/milky-way-nasa{{suffix}}.jpg".format(self.resource_folder),
        )

    def test_instance(self, storage):
        assert isinstance(storage.file.instance, self.resource_class)
        assert storage.file.instance is storage.resource

    def test_variation_name(self, storage):
        assert storage.file.variation_name == "desktop"

    def test_size(self, storage):
        # разный размер - зависит от версии Pillow
        assert storage.file.size in {115559, 112734, 129255, 126361}

    def test_variation(self, storage):
        assert isinstance(storage.file.variation, PaperVariation)
        assert storage.file.variation.name == "desktop"

    def test_path(self, storage):
        assert utils.match_path(
            storage.resource.path,
            "/media/{}/milky-way-nasa{{suffix}}.jpg".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert utils.match_path(
            storage.resource.url,
            "/media/{}/milky-way-nasa{{suffix}}.jpg".format(self.resource_folder),
        )

    def test_exists(self, storage):
        assert storage.file.exists() is True

    def test_width(self, storage):
        assert storage.file.width == 800

    def test_height(self, storage):
        assert storage.file.height == 577

    def test_read(self, storage):
        assert storage.file.closed is True
        with storage.file.open():
            assert storage.file.closed is False
        assert storage.file.closed is True

    def test_delete(self, storage):
        source_name = storage.file.name
        source_file = storage.file.path
        backup_file = os.path.join(settings.BASE_DIR, "media", self.resource_folder, "nasa.bak.jpg")
        shutil.copyfile(source_file, backup_file)

        storage.file.delete()
        assert storage.file.exists() is False

        with pytest.raises(ValueError):
            x = storage.file.path

        with pytest.raises(ValueError):
            x = storage.file.url

        with pytest.raises(ValueError):
            x = storage.file.size

        with pytest.raises(ValueError):
            storage.file.open()

        assert storage.file.exists() is False

        storage.file.name = source_name
        shutil.move(backup_file, source_file)

    def test_delete_unexisted(self, storage):
        source_name = storage.file.name
        source_file = storage.file.path
        backup_file = os.path.join(settings.BASE_DIR, "media", self.resource_folder, "nasa.bak.jpg")
        shutil.copyfile(source_file, backup_file)

        storage.file.delete()
        assert storage.file.exists() is False

        # call again
        storage.file.delete()

        storage.file.name = source_name
        shutil.move(backup_file, source_file)
