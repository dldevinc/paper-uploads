import datetime

import cloudinary.exceptions
import pytest
from cloudinary import uploader
from django.core.files import File
from django.utils.crypto import get_random_string
from examples.cloudinary.standard.models import Page

from paper_uploads import exceptions, helpers
from paper_uploads.cloudinary.models import CloudinaryMedia
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


class TestCloudinaryMedia(BacklinkModelTestMixin, TestFileFieldResource):
    resource_class = CloudinaryMedia
    resource_attachment = AUDIO_FILEPATH
    resource_basename = "audio"
    resource_extension = "mp3"
    resource_name = "files/%Y-%m-%d/audio{suffix}"
    resource_size = 2113939
    resource_checksum = "4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d"
    resource_folder = "files/%Y-%m-%d"
    owner_fieldname = "media"
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
        assert file_field.resource_type == "video"

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
        # no extension
        public_id = storage.resource.get_file().public_id
        assert utils.match_path(
            public_id,
            "{}/audio{{suffix}}".format(self.resource_folder),
        )

    def test_name(self, storage):
        # no extension
        assert utils.match_path(
            storage.resource.name,
            "{}/audio{{suffix}}".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert storage.resource.url.startswith("https://res.cloudinary.com/")
        assert utils.match_path(
            storage.resource.url,
            "{}/audio{{suffix}}.mp3".format(self.resource_folder),
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
            "file_info": "(mp3, 2.1\xa0MB)",
            "created": storage.resource.created_at.isoformat(),
            "modified": storage.resource.modified_at.isoformat(),
            "uploaded": storage.resource.uploaded_at.isoformat(),
        }

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b"ID3\x03"

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
        url = storage.resource.build_url(audio_frequency="44100")
        assert url.startswith("https://res.cloudinary.com/")
        assert "/af_44100/" in url


class TestCloudinaryMediaAttach(TestFileFieldResourceAttach):
    resource_class = CloudinaryMedia
    resource_attachment = VIDEO_FILEPATH
    resource_basename = "video"
    resource_extension = "avi"
    resource_size = 1496576
    resource_checksum = "68f7b2833c52df5ecfcb809509677f499acbe6a93cb1df79508a8ac0e1f7e3d3"

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
            with open(DOCUMENT_FILEPATH, "rb") as fp:
                with pytest.raises(exceptions.UnsupportedResource):
                    resource.attach(fp)


class TestCloudinaryMediaRename(BacklinkModelTestMixin, TestFileFieldResourceRename):
    resource_class = CloudinaryMedia
    resource_attachment = VIDEO_FILEPATH
    resource_size = 1496576
    resource_checksum = "68f7b2833c52df5ecfcb809509677f499acbe6a93cb1df79508a8ac0e1f7e3d3"
    owner_fieldname = "media"
    owner_model = Page
    old_name = "old_name_{}.mpeg".format(get_random_string(6))
    new_name = "new_name_{}.mp4".format(get_random_string(6))

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
        assert storage.resource.extension == "avi"


class TestCloudinaryMediaDelete(BacklinkModelTestMixin, TestFileFieldResourceDelete):
    resource_class = CloudinaryMedia
    resource_attachment = AUDIO_FILEPATH
    owner_fieldname = "media"
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
    recource_class = CloudinaryMedia
