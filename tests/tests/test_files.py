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
    @staticmethod
    def init_class(storage):
        storage.resource = DummyVersatileImageResource(
            owner_app_label='app',
            owner_model_name='dummyversatileimageresource',
            owner_fieldname='file'
        )
        with open(NASA_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        storage.file = VariationFile(storage.resource, 'desktop')

        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_name(self, storage):
        assert storage.file.name == utils.get_target_filepath(
            'versatile_image/milky-way-nasa{suffix}.desktop.jpg',
            storage.resource.name
        )

    def test_instance(self, storage):
        assert isinstance(storage.file.instance, DummyVersatileImageResource)
        assert storage.file.instance is storage.resource

    def test_variation_name(self, storage):
        assert storage.file.variation_name == 'desktop'

    def test_size(self, storage):
        assert storage.file.size == 115559

    def test_variation(self, storage):
        assert isinstance(storage.file.variation, PaperVariation)
        assert storage.file.variation.name == 'desktop'

    def test_path(self, storage):
        assert storage.resource.path.endswith(utils.get_target_filepath(
            '/media/versatile_image/milky-way-nasa{suffix}.jpg',
            storage.resource.get_file_url()
        ))

    def test_url(self, storage):
        assert storage.resource.url == utils.get_target_filepath(
            '/media/versatile_image/milky-way-nasa{suffix}.jpg',
            storage.resource.get_file_url()
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
        backup_file = os.path.join(settings.BASE_DIR, 'media/versatile_image/nasa.bak.jpg')
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
        backup_file = os.path.join(settings.BASE_DIR, 'media/versatile_image/nasa.bak.jpg')
        shutil.copyfile(source_file, backup_file)

        storage.file.delete()
        assert storage.file.exists() is False

        # call again
        storage.file.delete()

        storage.file.name = source_name
        shutil.move(backup_file, source_file)
