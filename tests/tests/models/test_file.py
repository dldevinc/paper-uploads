import os

from app.models import FileExample
from paper_uploads.models import UploadedFile

from ..dummy import *
from ..mixins import BacklinkModelTestMixin
from .test_dummy import (
    TestFileFieldResource,
    TestFileFieldResourceAttach,
    TestFileFieldResourceDelete,
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
)


class TestUploadedFile(BacklinkModelTestMixin, TestFileFieldResource):
    resource_url = "/media/files/%Y-%m-%d"
    resource_location = "files/%Y-%m-%d"
    resource_basename = "Nature Tree"
    resource_extension = "Jpeg"
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    owner_fieldname = "file"
    owner_model = FileExample
    file_field_name = "file"

    @classmethod
    def init_class(cls, storage):
        storage.resource = UploadedFile()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(NATURE_FILEPATH)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_basename

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            "id": 1,
            "name": self.resource_basename,
            "extension": self.resource_extension,
            "caption": "{}.{}".format(
                self.resource_basename,
                self.resource_extension
            ),
            "size": self.resource_size,
            "file_info": "(Jpeg, 672.8\xa0KB)",
            "url": storage.resource.get_file_url(),
            "created": storage.resource.created_at.isoformat(),
            "modified": storage.resource.modified_at.isoformat(),
            "uploaded": storage.resource.uploaded_at.isoformat(),
        }


class TestUploadedFileAttach(TestFileFieldResourceAttach):
    resource_class = UploadedFile


class TestUploadedFileRename(BacklinkModelTestMixin, TestFileFieldResourceRename):
    resource_class = UploadedFile
    resource_location = "files/%Y-%m-%d"
    owner_fieldname = "file"
    owner_model = FileExample

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(NATURE_FILEPATH, name="old_name.jpg")
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path

        storage.resource.rename("new_name.png")
        storage.resource.save()

        yield

        os.remove(storage.old_source_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestUploadedFileDelete(BacklinkModelTestMixin, TestFileFieldResourceDelete):
    resource_class = UploadedFile
    resource_location = "files/%Y-%m-%d"
    owner_fieldname = "file"
    owner_model = FileExample

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(NATURE_FILEPATH, name="old_name.jpg")
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.delete_file()

        yield

        storage.resource.delete()


class TestUploadedFileEmpty(TestFileFieldResourceEmpty):
    recource_class = UploadedFile


class TestUploadedFileExists(BacklinkModelTestMixin):
    owner_fieldname = "file"
    owner_model = FileExample

    @classmethod
    def init_class(cls, storage):
        storage.resource = UploadedFile()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(NATURE_FILEPATH)
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
