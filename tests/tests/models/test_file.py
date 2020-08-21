import os

from app.models import FileExample
from paper_uploads.models import UploadedFile

from .. import utils
from ..dummy import *
from .test_base import TestFileFieldResource


class TestUploadedFile(TestFileFieldResource):
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 672759
    resource_hash = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'

    @classmethod
    def init(cls, storage):
        storage.resource = UploadedFile(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_get_owner_model(self, storage):
        assert storage.resource.get_owner_model() is FileExample

    def test_get_owner_field(self, storage):
        assert storage.resource.get_owner_field() is FileExample._meta.get_field('file')

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg',
            file_name
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url == utils.get_target_filepath(
            '/media/files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg',
            file_url
        )

    def test_path(self, storage):
        assert storage.resource.path.endswith(utils.get_target_filepath(
            '/media/files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg',
            storage.resource.get_file_url()
        ))

    def test_url(self, storage):
        assert storage.resource.url == utils.get_target_filepath(
            '/media/files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg',
            storage.resource.get_file_url()
        )

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'file_info': '(Jpeg, 657.0\xa0KB)',
            'url': utils.get_target_filepath(
                '/media/files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg',
                storage.resource.get_file_url()
            ),
        }


class TestUploadedFileExists:
    @staticmethod
    def init(storage):
        storage.resource = UploadedFile(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_files(self, storage):
        source_path = storage.resource.path
        assert os.path.exists(source_path) is True
        storage.resource.delete_file()
        assert os.path.exists(source_path) is False
