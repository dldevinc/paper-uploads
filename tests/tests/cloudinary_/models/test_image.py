import datetime

import cloudinary.exceptions
import pytest
from cloudinary import uploader
from django.utils.crypto import get_random_string
from examples.cloudinary.standard.models import Page

from paper_uploads import exceptions
from paper_uploads.cloudinary.models import CloudinaryImage
from paper_uploads.cloudinary.models.base import CloudinaryFieldFile

from ... import utils
from ...dummy import *
from ...mixins import BacklinkModelTestMixin
from ...models.test_dummy import (
    TestImageFieldResource,
    TestImageFieldResourceAttach,
    TestImageFieldResourceDelete,
    TestImageFieldResourceEmpty,
    TestImageFieldResourceRename,
)


class TestCloudinaryImage(BacklinkModelTestMixin, TestImageFieldResource):
    resource_class = CloudinaryImage
    resource_attachment = CALLIPHORA_FILEPATH
    resource_basename = "calliphora"
    resource_extension = "jpg"
    resource_name = "images/%Y-%m-%d/calliphora{suffix}"
    resource_size = 254766
    resource_checksum = "d4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386"
    resource_folder = "images/%Y-%m-%d"
    resource_field_name = "file"
    owner_fieldname = "image"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            title="Nasa",
            description="Calliphora is a genus of blow flies, also known as bottle flies",
        )
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
        assert file_field.resource_type == "image"

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

    def test_public_id(self, storage):
        # no extension
        public_id = storage.resource.get_file().public_id
        assert utils.match_path(
            public_id,
            "{}/calliphora{{suffix}}".format(self.resource_folder),
        )

    def test_name(self, storage):
        # no extension
        assert utils.match_path(
            storage.resource.name,
            "{}/calliphora{{suffix}}".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert storage.resource.url.startswith("https://res.cloudinary.com/")
        assert utils.match_path(
            storage.resource.url,
            "{}/calliphora{{suffix}}.jpg".format(self.resource_folder),
            source=storage.resource.name
        )

    def test_title(self, storage):
        assert storage.resource.title == "Nasa"

    def test_description(self, storage):
        assert storage.resource.description == "Calliphora is a genus of blow flies, " \
                                               "also known as bottle flies"

    def test_width(self, storage):
        assert storage.resource.width == 804

    def test_height(self, storage):
        assert storage.resource.height == 1198

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
            "width": 804,
            "height": 1198,
            "cropregion": "",
            "title": "Nasa",
            "description": "Calliphora is a genus of blow flies, also known as bottle flies",
            "url": storage.resource.url,
            "file_info": "(jpg, 804x1198, 254.8\xa0KB)",
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
        url = storage.resource.build_url(width=100)
        assert url.startswith("https://res.cloudinary.com/")
        assert "/w_100/" in url


class TestCloudinaryImageAttach(TestImageFieldResourceAttach):
    resource_class = CloudinaryImage
    resource_attachment = CALLIPHORA_FILEPATH
    resource_basename = "calliphora"
    resource_extension = "jpg"
    resource_size = 254766
    resource_checksum = "d4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386"

    def test_unsupported_file(self):
        with self.get_resource() as resource:
            with open(DOCUMENT_FILEPATH, "rb") as fp:
                with pytest.raises(exceptions.UnsupportedResource):
                    resource.attach(fp)


class TestCloudinaryImageRename(TestImageFieldResourceRename):
    resource_class = CloudinaryImage
    resource_attachment = NASA_FILEPATH
    resource_size = 9711423
    resource_checksum = "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"
    owner_fieldname = "image"
    owner_model = Page
    old_name = "old_name_{}.tiff".format(get_random_string(6))
    new_name = "new_name_{}.tif".format(get_random_string(6))

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

    def test_extension(self, storage):
        assert storage.resource.extension == "jpg"


class TestCloudinaryImageDelete(TestImageFieldResourceDelete):
    resource_class = CloudinaryImage
    resource_attachment = NATURE_FILEPATH
    owner_fieldname = "image"
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


class TestCloudinaryFileEmpty(TestImageFieldResourceEmpty):
    recource_class = CloudinaryImage
