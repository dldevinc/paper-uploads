import os

from app.models import FileExample
from paper_uploads.models import UploadedFile

from ..dummy import *
from .test_base import (
    TestFileFieldResource,
    TestFileFieldResourceAttach,
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
    def init_class(cls, storage):
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

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'file_info': '(Jpeg, 672.8\xa0KB)',
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }


class TestUploadedFileAttach(TestFileFieldResourceAttach):
    resource_class = UploadedFile


class TestUploadedFileRename(TestFileFieldResourceRename):
    resource_class = UploadedFile
    resource_location = 'files/%Y-%m-%d'
    owner_app_label = 'app'
    owner_model_name = 'fileexample'
    owner_fieldname = 'file'

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
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


class TestUploadedFileDelete(TestFileFieldResourceDelete):
    resource_class = UploadedFile
    resource_location = 'files/%Y-%m-%d'
    owner_app_label = 'app'
    owner_model_name = 'fileexample'
    owner_fieldname = 'file'

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
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


class TestUploadedFileEmpty(TestFileFieldResourceEmpty):
    recource_class = UploadedFile


class TestUploadedFileExists:
    @staticmethod
    def init_class(storage):
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
