import os

from app.models import FileExample
from paper_uploads.models import UploadedFile

from .. import utils
from ..dummy import *
from .test_base import (
    TestFileFieldResource,
    TestFileFieldResourceDelete,
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
)


class TestUploadedFile(TestFileFieldResource):
    resource_url = '/media/files/%Y-%m-%d'
    resource_location = 'files/%Y-%m-%d'
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = 'app'
    owner_model_name = 'fileexample'
    owner_fieldname = 'file'
    owner_class = FileExample
    file_field_name = 'file'

    @classmethod
    def init(cls, storage):
        storage.resource = UploadedFile(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'file_info': '(Jpeg, 657.0\xa0KB)',
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }


class TestUploadedFileRename(TestFileFieldResourceRename):
    @classmethod
    def init(cls, storage):
        storage.resource = UploadedFile(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path

        storage.resource.rename_file('new_name.png')

        yield

        os.remove(storage.old_source_path)
        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            'files/%Y-%m-%d/old_name{suffix}.jpg',
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            'files/%Y-%m-%d/new_name{suffix}.png',
            file.name
        )


class TestUploadedFileDelete(TestFileFieldResourceDelete):
    @classmethod
    def init(cls, storage):
        storage.resource = UploadedFile(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            'files/%Y-%m-%d/old_name{suffix}.jpg',
            storage.old_source_name
        )


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

        try:
            storage.resource.delete_file()
        except ValueError:
            pass

        storage.resource.delete()

    def test_files(self, storage):
        source_path = storage.resource.path
        assert os.path.exists(source_path) is True
        storage.resource.delete_file()
        assert os.path.exists(source_path) is False


class TestEmptyUploadedFile(TestFileFieldResourceEmpty):
    @classmethod
    def init(cls, storage):
        storage.resource = UploadedFile()
        yield
