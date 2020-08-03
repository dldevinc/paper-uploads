import os

from app.models import ImageExample
from paper_uploads.models import UploadedImage

from .. import utils
from ..dummy import *
from .test_base import TestVersatileImageResource


class TestUploadedImage(TestVersatileImageResource):
    @staticmethod
    def init(storage):
        storage.resource = UploadedImage(
            title='Calliphora',
            description='Calliphora is a genus of blow flies, also known as bottle flies',
            owner_app_label='app',
            owner_model_name='imageexample',
            owner_fieldname='image'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_owner_model(self, storage):
        assert storage.resource.get_owner_model() is ImageExample

    def test_get_owner_field(self, storage):
        assert storage.resource.get_owner_field() is ImageExample._meta.get_field('image')

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'images/%Y-%m-%d/Nature_Tree.Jpeg',
            file_name
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url == utils.get_target_filepath(
            '/media/images/%Y-%m-%d/Nature_Tree.Jpeg',
            file_url
        )

    def test_path(self, storage):
        assert storage.resource.path.endswith(utils.get_target_filepath(
            '/media/images/%Y-%m-%d/Nature_Tree.Jpeg',
            storage.resource.get_file_url()
        ))

    def test_url(self, storage):
        assert storage.resource.url == utils.get_target_filepath(
            '/media/images/%Y-%m-%d/Nature_Tree.Jpeg',
            storage.resource.get_file_url()
        )

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': 'Nature Tree',
            'extension': 'Jpeg',
            'size': 672759,
            'width': 1534,
            'height': 2301,
            'title': 'Calliphora',
            'description': 'Calliphora is a genus of blow flies, also known as bottle flies',
            'cropregion': '',
            'file_info': '(Jpeg, 1534x2301, 657.0\xa0KB)',
            'url': utils.get_target_filepath(
                '/media/images/%Y-%m-%d/Nature_Tree{}.Jpeg',
                storage.resource.get_file_url()
            ),
        }


class TestUploadedImageExists:
    @staticmethod
    def init(storage):
        storage.resource = UploadedImage(
            owner_app_label='app',
            owner_model_name='imageexample',
            owner_fieldname='image'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_files(self, storage):
        source_path = storage.resource.path
        desktop_path = storage.resource.desktop.path
        mobile_path = storage.resource.mobile.path

        assert os.path.exists(source_path) is True
        assert os.path.exists(desktop_path) is True
        assert os.path.exists(mobile_path) is True

        storage.resource.delete_file()

        assert os.path.exists(source_path) is False
        assert os.path.exists(desktop_path) is False
        assert os.path.exists(mobile_path) is False
