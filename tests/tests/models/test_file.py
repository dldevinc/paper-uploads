import os

from django.utils.crypto import get_random_string
from examples.fields.standard.models import Page

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
    resource_class = UploadedFile
    resource_attachment = NATURE_FILEPATH
    resource_basename = "Nature Tree"
    resource_extension = "Jpeg"
    resource_name = "files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg"
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    resource_folder = "files/%Y-%m-%d"
    resource_field_name = "file"
    owner_fieldname = "file"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(cls.resource_attachment)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

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
            "url": storage.resource.url,
            "file_info": "(Jpeg, 672.8\xa0KB)",
            "created": storage.resource.created_at.isoformat(),
            "modified": storage.resource.modified_at.isoformat(),
            "uploaded": storage.resource.uploaded_at.isoformat(),
        }


class TestUploadedFileAttach(TestFileFieldResourceAttach):
    resource_class = UploadedFile
    resource_attachment = DOCUMENT_FILEPATH
    resource_basename = "document"
    resource_extension = "pdf"
    resource_size = 3028
    resource_checksum = "93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e"


class TestUploadedFileRename(BacklinkModelTestMixin, TestFileFieldResourceRename):
    resource_class = UploadedFile
    resource_attachment = DOCUMENT_FILEPATH
    resource_size = 3028
    resource_checksum = "93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e"
    owner_fieldname = "file"
    owner_model = Page
    old_name = "old_name_{}.txt".format(get_random_string(6))
    new_name = "new_name_{}.log".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name
        storage.old_resource_path = storage.resource.path

        storage.resource.rename(cls.new_name)
        yield

        os.unlink(storage.old_resource_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestUploadedFileDelete(BacklinkModelTestMixin, TestFileFieldResourceDelete):
    resource_class = UploadedFile
    resource_attachment = EXCEL_FILEPATH
    owner_fieldname = "file"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(
            cls.resource_attachment,
            name="file_{}.jpg".format(get_random_string(6))
        )
        storage.resource.save()

        storage.old_resource_name = storage.resource.name

        storage.resource.delete_file()
        yield

        storage.resource.delete()


class TestUploadedFileEmpty(TestFileFieldResourceEmpty):
    recource_class = UploadedFile
