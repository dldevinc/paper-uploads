import datetime

import cloudinary.exceptions
import pytest
from cloudinary import uploader
from django.core.files import File
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from examples.cloudinary.collections.models import MixedCollection

from paper_uploads import exceptions, helpers
from paper_uploads.cloudinary.models import (
    CloudinaryFileItem,
    CloudinaryImageItem,
    CloudinaryMediaItem,
)
from paper_uploads.cloudinary.models.base import CloudinaryFieldFile

from ... import utils
from ...dummy import *
from ...models.test_collection import (
    CollectionItemAttachTestBase,
    CollectionItemDeleteTestBase,
    CollectionItemTestBase,
)
from ...models.test_dummy import (
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
    TestImageFieldResourceRename,
    TestVersatileImageEmpty,
)


class TestFileItem(CollectionItemTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryFileItem
    resource_attachment = EXCEL_FILEPATH
    resource_basename = "table"
    resource_extension = "xls"
    resource_name = "collections/files/%Y-%m-%d/table{suffix}.xls"
    resource_size = 8704
    resource_checksum = "c9c8ad905aa5142731b1e8ab34d5862f871627fa7ad8005264494c2489d2061e"
    resource_folder = "collections/files/%Y-%m-%d"
    resource_field_name = "file"

    def test_get_file_storage(self, storage):
        pass

    def test_path(self, storage):
        pass

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_basename

    def test_item_type(self, storage):
        assert storage.resource.type == "file"

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == "private"
        assert file_field.resource_type == "raw"

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        assert utils.match_path(
            public_id,
            "{}/table{{suffix}}.xls".format(self.resource_folder),
        )

    def test_get_file(self, storage):
        assert isinstance(storage.resource.get_file(), CloudinaryFieldFile)

    def test_name(self, storage):
        assert utils.match_path(
            storage.resource.name,
            "{}/table{{suffix}}.xls".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert storage.resource.url.startswith("https://res.cloudinary.com/")
        assert utils.match_path(
            storage.resource.url,
            "{}/table{{suffix}}.xls".format(self.resource_folder),
            source=storage.resource.name
        )

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'\xd0\xcf\x11\xe0'

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            "id": 1,
            "collectionId": 1,
            "itemType": "file",
            "type": "file",
            "name": self.resource_basename,
            "extension": self.resource_extension,
            "caption": "{}.{}".format(
                self.resource_basename,
                self.resource_extension
            ),
            "size": self.resource_size,
            "order": 0,
            "preview": render_to_string(
                "paper_uploads/items/preview/file.html",
                storage.resource.get_preview_context()
            ),
            "url": storage.resource.get_file_url(),
            "created": storage.resource.created_at.isoformat(),
            "modified": storage.resource.modified_at.isoformat(),
            "uploaded": storage.resource.uploaded_at.isoformat(),
        }

    def test_accept(self, storage):
        with open(EXCEL_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(NATURE_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(MEDITATION_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True


@pytest.mark.django_db
class TestFileItemAttach(CollectionItemAttachTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryFileItem
    resource_attachment = DOCUMENT_FILEPATH
    resource_basename = "document"
    resource_extension = "pdf"
    resource_size = 3028
    resource_checksum = "93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e"


class TestFileItemRename(TestFileFieldResourceRename):
    collection_class = MixedCollection
    resource_class = CloudinaryFileItem
    resource_attachment = DOCUMENT_FILEPATH
    resource_size = 3028
    resource_checksum = "93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e"
    old_name = "old_name_{}.txt".format(get_random_string(6))
    new_name = "new_name_{}.log".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name

        storage.resource.rename(cls.new_name)
        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

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


class TestFileItemDelete(CollectionItemDeleteTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryFileItem
    resource_attachment = EXCEL_FILEPATH

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


class TestFileItemEmpty(TestFileFieldResourceEmpty):
    collection_class = MixedCollection
    recource_class = CloudinaryFileItem


class TestMediaItem(CollectionItemTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryMediaItem
    resource_attachment = VIDEO_FILEPATH
    resource_basename = "video"
    resource_extension = "avi"
    resource_name = "collections/files/%Y-%m-%d/video{suffix}"
    resource_size = 1496576
    resource_checksum = "68f7b2833c52df5ecfcb809509677f499acbe6a93cb1df79508a8ac0e1f7e3d3"
    resource_folder = "collections/files/%Y-%m-%d"
    resource_field_name = "file"

    def test_get_file_storage(self, storage):
        pass

    def test_path(self, storage):
        pass

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_basename

    def test_item_type(self, storage):
        assert storage.resource.type == "media"

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == "private"
        assert file_field.resource_type == "video"

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        assert utils.match_path(
            public_id,
            "{}/video{{suffix}}".format(self.resource_folder),
        )

    def test_repr(self, storage):
        assert utils.match_path(
            repr(storage.resource),
            "{}('{}')".format(
                type(storage.resource).__name__,
                datetime.datetime.now().strftime(self.resource_name)
            ),
            source=storage.resource.name
        )

    def test_get_file(self, storage):
        assert isinstance(storage.resource.get_file(), CloudinaryFieldFile)

    def test_name(self, storage):
        assert utils.match_path(
            storage.resource.name,
            "{}/video{{suffix}}".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert storage.resource.url.startswith("https://res.cloudinary.com/")
        assert utils.match_path(
            storage.resource.url,
            "{}/video{{suffix}}.avi".format(self.resource_folder),
            source=storage.resource.name
        )

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'RIFF'

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            "id": 1,
            "collectionId": 1,
            "itemType": "media",
            "type": "media",
            "name": self.resource_basename,
            "extension": self.resource_extension,
            "caption": "{}.{}".format(
                self.resource_basename,
                self.resource_extension
            ),
            "size": self.resource_size,
            "order": 0,
            "preview": render_to_string(
                "paper_uploads/items/preview/file.html",
                storage.resource.get_preview_context()
            ),
            "url": storage.resource.get_file_url(),
            "created": storage.resource.created_at.isoformat(),
            "modified": storage.resource.modified_at.isoformat(),
            "uploaded": storage.resource.uploaded_at.isoformat(),
        }

    def test_accept(self, storage):
        with open(EXCEL_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(MEDITATION_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(AUDIO_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True


@pytest.mark.django_db
class TestMediaItemAttach(CollectionItemAttachTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryMediaItem
    resource_attachment = AUDIO_FILEPATH
    resource_basename = "audio"
    resource_extension = "mp3"
    resource_size = 2113939
    resource_checksum = "4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d"

    def test_django_file(self):
        with self.get_resource() as resource:
            overriden_name = "milky-way-nasa_{}.mp4".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_django_file_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/milky-way-nasa_{}.mp4".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.mp4".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/overwritten_{}.mp4".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_django_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.mp4".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="not_used.png")
                resource.attach(file, name=overriden_name)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_django_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.mp4".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="photos/not_used.png")
                resource.attach(file, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_unsupported_file(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, "rb") as fp:
                with pytest.raises(exceptions.UnsupportedResource):
                    resource.attach(fp)


class TestMediaItemRename(TestFileFieldResourceRename):
    collection_class = MixedCollection
    resource_class = CloudinaryMediaItem
    resource_attachment = AUDIO_FILEPATH
    resource_size = 2113939
    resource_checksum = "4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d"
    old_name = "old_name_{}.mpeg".format(get_random_string(6))
    new_name = "new_name_{}.mp4".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name

        storage.resource.rename(cls.new_name)
        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

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
        assert storage.resource.extension == "mp3"


class TestMediaItemDelete(CollectionItemDeleteTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryMediaItem
    resource_attachment = AUDIO_FILEPATH

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


class TestMediaItemEmpty(TestFileFieldResourceEmpty):
    collection_class = MixedCollection
    recource_class = CloudinaryMediaItem


class TestImageItem(CollectionItemTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryImageItem
    resource_attachment = CALLIPHORA_FILEPATH
    resource_basename = "calliphora"
    resource_extension = "jpg"
    resource_name = "collections/images/%Y-%m-%d/calliphora{suffix}"
    resource_size = 254766
    resource_checksum = "d4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386"
    resource_folder = "collections/images/%Y-%m-%d"
    resource_field_name = "file"

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class(
            title="Nasa",
            description="Calliphora is a genus of blow flies, also known as bottle flies",
        )
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_storage(self, storage):
        pass

    def test_path(self, storage):
        pass

    def test_item_type(self, storage):
        assert storage.resource.type == "image"

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == "private"
        assert file_field.resource_type == "image"

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        assert utils.match_path(
            public_id,
            "{}/calliphora{{suffix}}".format(self.resource_folder),
        )

    def test_repr(self, storage):
        assert utils.match_path(
            repr(storage.resource),
            "{}('{}')".format(
                type(storage.resource).__name__,
                datetime.datetime.now().strftime(self.resource_name)
            ),
            source=storage.resource.name
        )

    def test_get_file(self, storage):
        assert isinstance(storage.resource.get_file(), CloudinaryFieldFile)

    def test_name(self, storage):
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

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            "id": 1,
            "collectionId": 1,
            "itemType": "image",
            "type": "image",
            "name": self.resource_basename,
            "extension": self.resource_extension,
            "caption": "{}.{}".format(
                self.resource_basename,
                self.resource_extension
            ),
            "size": self.resource_size,
            "order": 0,
            "width": 804,
            "height": 1198,
            "cropregion": "",
            "title": "Nasa",
            "description": "Calliphora is a genus of blow flies, also known as bottle flies",
            "preview": render_to_string(
                "paper_uploads_cloudinary/items/preview/image.html",
                storage.resource.get_preview_context()
            ),
            "url": storage.resource.get_file_url(),
            "created": storage.resource.created_at.isoformat(),
            "modified": storage.resource.modified_at.isoformat(),
            "uploaded": storage.resource.uploaded_at.isoformat(),
        }

    def test_accept(self, storage):
        with open(EXCEL_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(MEDITATION_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False


@pytest.mark.django_db
class TestImageItemAttach(CollectionItemAttachTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryImageItem
    resource_attachment = NASA_FILEPATH
    resource_basename = "milky-way-nasa"
    resource_extension = "jpg"
    resource_size = 9711423
    resource_checksum = "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"

    def test_django_file(self):
        with self.get_resource() as resource:
            overriden_name = "milky-way-nasa_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_django_file_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/milky-way-nasa_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/overwritten_{}.gif".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_django_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="not_used.png")
                resource.attach(file, name=overriden_name)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_django_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="photos/not_used.png")
                resource.attach(file, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_unsupported_file(self):
        with self.get_resource() as resource:
            with open(EXCEL_FILEPATH, "rb") as fp:
                with pytest.raises(exceptions.UnsupportedResource):
                    resource.attach(fp)


class TestImageItemRename(TestImageFieldResourceRename):
    collection_class = MixedCollection
    resource_class = CloudinaryImageItem
    resource_attachment = NASA_FILEPATH
    resource_size = 9711423
    resource_checksum = "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"
    old_name = "old_name_{}.tiff".format(get_random_string(6))
    new_name = "new_name_{}.tif".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name

        storage.resource.rename(cls.new_name)
        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

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


class TestImageItemDelete(CollectionItemDeleteTestBase):
    collection_class = MixedCollection
    resource_class = CloudinaryImageItem
    resource_attachment = NATURE_FILEPATH

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


class TestImageItemEmpty(TestVersatileImageEmpty):
    collection_class = MixedCollection
    recource_class = CloudinaryImageItem
