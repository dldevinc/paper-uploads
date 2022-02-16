import datetime

import cloudinary.exceptions
import pytest
from cloudinary import uploader
from django.utils.crypto import get_random_string
from examples.cloudinary.standard.models import Page

from paper_uploads.cloudinary.models import CloudinaryFile
from paper_uploads.cloudinary.models.base import CloudinaryFieldFile

from ... import utils
from ...dummy import *
from ...mixins import BacklinkModelTestMixin
from ...models.test_dummy import (
    TestFileFieldResource,
    TestFileFieldResourceAttach,
    TestFileFieldResourceDelete,
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
)


class TestCloudinaryFile(BacklinkModelTestMixin, TestFileFieldResource):
    resource_class = CloudinaryFile
    resource_attachment = NATURE_FILEPATH
    resource_basename = "Nature Tree"
    resource_extension = "Jpeg"
    resource_name = "files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg"
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    resource_folder = "files/%Y-%m-%d"
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

    def test_get_file_storage(self, storage):
        pass

    def test_path(self, storage):
        pass

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == "private"
        assert file_field.resource_type == "raw"

    def test_get_file(self, storage):
        assert isinstance(storage.resource.get_file(), CloudinaryFieldFile)

    def test_repr(self, storage):
        assert utils.match_path(
            repr(storage.resource),
            "{}('{}')".format(
                type(storage.resource).__name__,
                datetime.datetime.now().strftime(self.resource_name)
            ),
            source=storage.resource.name
        )

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_basename

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        assert utils.match_path(
            public_id,
            "{}/Nature_Tree{{suffix}}.Jpeg".format(self.resource_folder),
        )

    def test_name(self, storage):
        assert utils.match_path(
            storage.resource.name,
            "{}/Nature_Tree{{suffix}}.Jpeg".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert storage.resource.url.startswith("https://res.cloudinary.com/")
        assert utils.match_path(
            storage.resource.url,
            "{}/Nature_Tree{{suffix}}.Jpeg".format(self.resource_folder),
            source=storage.resource.name
        )

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

    def test_get_cloudinary_options(self, storage):
        options = storage.resource.get_cloudinary_options()
        assert options == {
            "use_filename": True,
            "unique_filename": True,
            "overwrite": True,
            "invalidate": True,
            "folder": datetime.datetime.now().strftime(self.resource_folder)
        }

    def test_build_url(self, storage):
        url = storage.resource.build_url(version="1.0.0")
        assert url.startswith("https://res.cloudinary.com/")
        assert "1.0.0" in url


class TestCloudinaryFileAttach(TestFileFieldResourceAttach):
    resource_class = CloudinaryFile


class TestCloudinaryFileRename(BacklinkModelTestMixin, TestFileFieldResourceRename):
    resource_class = CloudinaryFile
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

        storage.resource.rename(cls.new_name)
        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_existence(self, storage):
        file = storage.resource.get_file()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_resource_name,
                type=file.resource.type,
                resource_type=file.resource.resource_type
            )

    def test_new_file_existence(self, storage):
        file = storage.resource.get_file()
        uploader.explicit(
            file.name,
            type=file.resource.type,
            resource_type=file.resource.resource_type
        )


class TestCloudinaryFileDelete(BacklinkModelTestMixin, TestFileFieldResourceDelete):
    resource_class = CloudinaryFile
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

    def test_file_existence(self, storage):
        file_field = storage.resource.get_file_field()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_resource_name,
                type=file_field.type,
                resource_type=file_field.resource_type
            )

    def test_file_field_empty(self, storage):
        assert storage.resource.get_file() is None


class TestCloudinaryFileEmpty(TestFileFieldResourceEmpty):
    recource_class = CloudinaryFile
