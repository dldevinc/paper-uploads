import os

from django.utils.crypto import get_random_string
from examples.fields.standard.models import Page

from paper_uploads.models import UploadedImage
from paper_uploads.variations import PaperVariation

from ..dummy import *
from ..mixins import BacklinkModelTestMixin
from .test_dummy import (
    TestVersatileImageAttach,
    TestVersatileImageDelete,
    TestVersatileImageEmpty,
    TestVersatileImageRename,
    TestVersatileImageResource,
)


class TestUploadedImage(BacklinkModelTestMixin, TestVersatileImageResource):
    resource_class = UploadedImage
    resource_attachment = CALLIPHORA_FILEPATH
    resource_basename = "calliphora"
    resource_extension = "jpg"
    resource_name = "images/%Y-%m-%d/calliphora{suffix}.jpg"
    resource_folder = "images/%Y-%m-%d"
    resource_field_name = "file"
    owner_fieldname = "image_group"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            title="Calliphora",
            description="Calliphora is a genus of blow flies, also known as bottle flies",
        )
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(cls.resource_attachment)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_title(self, storage):
        assert storage.resource.title == "Calliphora"

    def test_calculate_max_size(self, storage):
        assert storage.resource.calculate_max_size((3000, 2000)) == (1800, 1200)
        assert storage.resource.calculate_max_size((2000, 3000)) == (800, 1200)

    def test_get_variations(self, storage):
        variations = storage.resource.get_variations()
        assert len(variations) == 5
        assert set(variations.keys()) == {"desktop", "mobile", "mobile_webp", "mobile_2x", "mobile_webp_2x"}
        assert all(isinstance(v, PaperVariation) for v in variations.values()) is True

    def test_variation_files(self, storage):
        assert dict(storage.resource.variation_files()) == {
            "desktop": storage.resource.desktop,
            "mobile": storage.resource.mobile,
            "mobile_webp": storage.resource.mobile_webp,
            "mobile_2x": storage.resource.mobile_2x,
            "mobile_webp_2x": storage.resource.mobile_webp_2x,
        }

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
            "title": "Calliphora",
            "description": "Calliphora is a genus of blow flies, also known as bottle flies",
            "url": storage.resource.url,
            "file_info": "(jpg, 804x1198, 254.8\xa0KB)",
            "created": storage.resource.created_at.isoformat(),
            "modified": storage.resource.modified_at.isoformat(),
            "uploaded": storage.resource.uploaded_at.isoformat(),
        }


class TestUploadedImageAttach(TestVersatileImageAttach):
    resource_class = UploadedImage
    resource_attachment = NASA_FILEPATH
    resource_basename = "milky-way-nasa"
    resource_extension = "jpg"
    resource_size = 9711423
    resource_checksum = "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"


class TestUploadedImageRename(BacklinkModelTestMixin, TestVersatileImageRename):
    resource_class = UploadedImage
    resource_attachment = NATURE_FILEPATH
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    owner_fieldname = "image_group"
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
        storage.old_resource_path = storage.resource.path
        storage.old_resource_desktop_path = storage.resource.desktop.path
        storage.old_resource_mobile_path = storage.resource.mobile.path
        storage.old_resource_mobile_2x_path = storage.resource.mobile_2x.path
        storage.old_resource_mobile_webp_path = storage.resource.mobile_webp.path
        storage.old_resource_mobile_webp_2x_path = storage.resource.mobile_webp_2x.path

        storage.resource.rename(cls.new_name)
        yield

        os.unlink(storage.old_resource_path)
        os.unlink(storage.old_resource_desktop_path)
        os.unlink(storage.old_resource_mobile_path)
        os.unlink(storage.old_resource_mobile_2x_path)
        os.unlink(storage.old_resource_mobile_webp_path)
        os.unlink(storage.old_resource_mobile_webp_2x_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestUploadedImageDelete(BacklinkModelTestMixin, TestVersatileImageDelete):
    resource_class = UploadedImage
    resource_attachment = NASA_FILEPATH
    owner_fieldname = "image_group"
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


class TestUploadedImageEmpty(TestVersatileImageEmpty):
    recource_class = UploadedImage
