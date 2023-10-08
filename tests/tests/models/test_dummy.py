import io
import os
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

import pytest
from django.core.files import File
from django.utils.crypto import get_random_string

from app.models import *
from paper_uploads import helpers, signals
from paper_uploads.exceptions import UnsupportedResource
from paper_uploads.files import VariationFile
from paper_uploads.storage import default_storage
from paper_uploads.variations import PaperVariation

from .. import utils
from ..dummy import *
from ..mixins import FileProxyTestMixin


class TestResource:
    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyResource.objects.create()
        yield
        storage.resource.delete()

    def test_created_at(self, storage):
        assert utils.is_equal_dates(storage.resource.created_at, storage.now)

    def test_modified_at(self, storage):
        assert utils.is_equal_dates(storage.resource.modified_at, storage.now)

    def test_created_at_less_than_modified_at(self, storage):
        assert storage.resource.created_at < storage.resource.modified_at

    def test_repr(self, storage):
        assert repr(storage.resource) == "{} #{}".format(
            type(storage.resource).__name__,
            storage.resource.pk
        )

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
            },
            ignore={"id"}
        )


class TestFileResource(FileProxyTestMixin, TestResource):
    resource_class = DummyFileResource
    resource_basename = "Nature Tree_{}".format(get_random_string(6))
    resource_extension = "Jpeg"
    resource_name = "/tmp/{}{{suffix}}.Jpeg".format(resource_basename)
    resource_size = 13
    resource_checksum = "6246efc88ae4aa025e48c9c7adc723d5c97171a1fa6233623c7251ab8e57602f"
    resource_mimetype = "text/plain"

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        filename = "{}.{}".format(cls.resource_basename, cls.resource_extension)
        storage.resource.attach(File(io.BytesIO(b"Hello, world!"), name=filename))
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_has_meta(self):
        assert hasattr(self.resource_class, "_resource_meta")

    def test_meta_options(self):
        opts = self.resource_class._resource_meta
        assert opts.required_fields == []

    def test_resource_name(self, storage):
        assert storage.resource.resource_name == self.resource_basename

    def test_extension(self, storage):
        assert storage.resource.extension == self.resource_extension

    def test_size(self, storage):
        assert storage.resource.size == self.resource_size

    def test_checksum(self, storage):
        assert storage.resource.checksum == self.resource_checksum

    def test_mimetype(self, storage):
        assert storage.resource.mimetype == self.resource_mimetype

    def test_uploaded_at(self, storage):
        assert utils.is_equal_dates(storage.resource.uploaded_at, storage.now)
        assert utils.is_equal_dates(storage.resource.uploaded_at, storage.resource.modified_at)

    def test_str(self, storage):
        assert str(storage.resource) == storage.resource.get_caption()

    def test_repr(self, storage):
        assert utils.match_path(
            repr(storage.resource),
            "{}('{}')".format(
                type(storage.resource).__name__,
                self.resource_name
            )
        )

    def test_name(self, storage):
        assert utils.match_path(
            storage.resource.name,
            self.resource_name
        )

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "mimetype": self.resource_mimetype,
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id"}
        )

    def test_read(self, storage):
        with storage.resource.open("r") as fp:
            assert fp.read(5) == "Hello"

    def test_writable(self, storage):
        with storage.resource.open() as fp:
            assert fp.writable() is False

    def test_multiple_chunks(self, storage, chunk_size=1024):
        return super().test_multiple_chunks(storage, chunk_size=8)

    def test_update_checksum(self, storage):
        storage.resource.checksum = ""

        assert storage.resource.update_checksum(storage.resource.get_file()) is True
        assert storage.resource.checksum == self.resource_checksum

        assert storage.resource.update_checksum(storage.resource.get_file()) is False  # not updated
        assert storage.resource.checksum == self.resource_checksum

    def test_get_caption(self, storage):
        assert storage.resource.get_caption() == "{}.{}".format(
            self.resource_basename,
            self.resource_extension
        )

    def test_get_caption_without_extension(self, storage):
        ext = storage.resource.extension
        storage.resource.extension = ""
        assert storage.resource.get_caption() == self.resource_basename
        storage.resource.extension = ext

    def test_get_file(self, storage):
        assert isinstance(storage.resource.get_file(), File)

    def test_get_file_size(self, storage):
        assert storage.resource.get_file_size() == self.resource_size

    def test_file_exists(self, storage):
        assert storage.resource.file_exists() is True

    def test_file_not_exists(self):
        resource = self.resource_class()
        resource.resource_name = "non-existent-file"
        resource.extension = self.resource_extension
        assert resource.file_exists() is False


class TestEmptyFileResource:
    resource_class = DummyFileResource

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        yield

    def test_resource_name(self, storage):
        assert storage.resource.resource_name == ""

    def test_extension(self, storage):
        assert storage.resource.extension == ""

    def test_size(self, storage):
        assert storage.resource.size == 0

    def test_checksum(self, storage):
        assert storage.resource.checksum == ""

    def test_mimetype(self, storage):
        assert storage.resource.mimetype == ""

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": None,
                "name": "",
                "extension": "",
                "caption": "",
                "size": 0,
                "mimetype": "",
                "created": storage.resource.created_at.isoformat(),
                "modified": None,
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id"}
        )

    def test_name(self, storage):
        assert storage.resource.name == ""

    def test_get_file(self, storage):
        assert bool(storage.resource.get_file()) is False

    def test_get_caption(self, storage):
        assert storage.resource.get_caption() == ""

    def test_get_file_size(self, storage):
        assert storage.resource.get_file_size() == 0

    def test_file_exists(self, storage):
        assert storage.resource.file_exists() is False

    def test_open(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.resource.open()

    def test_closed(self, storage):
        assert storage.resource.closed is True

    def test_rename_file(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.resource.rename("bla-bla.jpg")

    def test_delete_file(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.resource.delete_file()


class TestFileResourceAttach:
    resource_class = DummyFileResource
    resource_attachment = NASA_FILEPATH
    resource_basename = "milky-way-nasa"
    resource_extension = "jpg"
    resource_size = 9711423
    resource_checksum = "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"
    resource_mimetype = "image/jpeg"

    @contextmanager
    def get_resource(self):
        resource = self.resource_class()
        try:
            yield resource
        finally:
            resource.delete_file()

    def test_string(self):
        with self.get_resource() as resource:
            resource.attach(self.resource_attachment)

            assert resource.resource_name == self.resource_basename
            assert resource.extension == self.resource_extension
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum
            assert resource.mimetype == self.resource_mimetype

    def test_pathlib(self):
        with self.get_resource() as resource:
            resource.attach(Path(self.resource_attachment))

            assert resource.resource_name == self.resource_basename
            assert resource.extension == self.resource_extension
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum
            assert resource.mimetype == self.resource_mimetype

    def test_file(self):
        with self.get_resource() as resource:
            with open(self.resource_attachment, "rb") as fp:
                resource.attach(fp)

            assert resource.resource_name == self.resource_basename
            assert resource.extension == self.resource_extension
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum
            assert resource.mimetype == self.resource_mimetype

    def test_django_file(self):
        with self.get_resource() as resource:
            overriden_name = "milky-way-nasa_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == helpers.get_extension(overriden_name)

    def test_django_file_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/milky-way-nasa_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == helpers.get_extension(overriden_name)

    def test_override_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == helpers.get_extension(overriden_name)

    def test_override_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/overwritten_{}.gif".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == helpers.get_extension(overriden_name)

    def test_override_django_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="not_used.png")
                resource.attach(file, name=overriden_name)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == helpers.get_extension(overriden_name)

    def test_override_django_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="photos/not_used.png")
                resource.attach(file, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == helpers.get_extension(overriden_name)

    def test_file_position(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.jpg".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                resource.attach(fp, name=overriden_name)
                assert fp.tell() == self.resource_size


class TestFileResourceRename:
    resource_class = DummyFileResource
    resource_attachment = NATURE_FILEPATH
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    resource_mimetype = "image/jpeg"
    old_name = "old_name_{}.txt".format(get_random_string(6))
    new_name = "new_name_{}.log".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name

        storage.resource.rename(cls.new_name)
        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_existence(self, storage):
        assert os.path.exists(storage.old_resource_name) is False

    def test_new_file_existence(self, storage):
        assert os.path.exists(storage.resource.name) is True

    def test_resource_name(self, storage):
        assert storage.resource.resource_name == helpers.get_filename(self.new_name)

    def test_extension(self, storage):
        assert storage.resource.extension == helpers.get_extension(self.new_name)

    def test_size(self, storage):
        assert storage.resource.size == self.resource_size

    def test_checksum(self, storage):
        assert storage.resource.checksum == self.resource_checksum

    def test_mimetype(self, storage):
        assert storage.resource.mimetype == self.resource_mimetype

    def test_modified_at_updated(self, storage):
        assert storage.resource.modified_at > storage.old_modified_at


class TestFileResourceDelete:
    resource_class = DummyFileResource
    resource_attachment = NATURE_FILEPATH

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
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
        assert os.path.exists(storage.old_resource_name) is False


class TestFileResourceSignals:
    resource_class = DummyFileResource

    def test_update_checksum(self):
        resource = self.resource_class()
        resource.attach(NATURE_FILEPATH, name="name_{}.jpg".format(get_random_string(6)))
        resource.checksum = ""
        signal_fired = False

        def signal_handler(sender, instance, checksum, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is self.resource_class
            assert instance is resource
            assert checksum == "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"

        signals.checksum_update.connect(signal_handler)
        assert signal_fired is False
        assert resource.update_checksum(resource.get_file()) is True
        assert signal_fired is True
        signals.checksum_update.disconnect(signal_handler)

        resource.delete_file()

    def test_pre_attach_file(self):
        resource = self.resource_class()
        signal_fired = False

        def signal_handler(sender, instance, file, options, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is self.resource_class
            assert instance is resource

            # ensure instance not filled yet
            assert instance.resource_name == ""
            assert instance.extension == ""
            assert instance.size == 0
            assert instance.checksum == ""

            # ensure file type
            assert isinstance(file, File)

            # ensure original file
            assert file.size == 9711423

            # extra parameters passed to `attach()`
            assert options == {
                "key1": "value1",
                "key2": "value2"
            }

        signals.pre_attach_file.connect(signal_handler)
        assert signal_fired is False
        resource.attach(
            NASA_FILEPATH,
            name="name_{}.jpg".format(get_random_string(6)),
            key1="value1",
            key2="value2"
        )
        assert signal_fired is True
        signals.pre_attach_file.disconnect(signal_handler)

        resource.delete_file()

    def test_post_attach_file(self):
        resource = self.resource_class()
        filename = "name_{}.jpg".format(get_random_string(6))
        signal_fired = False

        def signal_handler(sender, instance, file, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is self.resource_class
            assert instance is resource

            # ensure instance filled
            assert instance.resource_name == helpers.get_filename(filename)
            assert instance.extension == helpers.get_extension(filename)
            assert instance.size == 9711423
            assert instance.checksum == "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"

            # ensure file type
            assert isinstance(file, File)

            # check file position
            if file.seekable():
                assert file.tell() == 0

            # extra parameters passed to `attach()`
            assert options == {
                "key1": "value1",
                "key2": "value2"
            }

            # result of `_attach()` method
            assert response == {
                "success": True,
            }

        signals.post_attach_file.connect(signal_handler)
        assert signal_fired is False
        resource.attach(
            NASA_FILEPATH,
            name=filename,
            key1="value1",
            key2="value2"
        )
        assert signal_fired is True
        signals.post_attach_file.disconnect(signal_handler)

        resource.delete_file()

    def test_pre_rename_file(self):
        resource = self.resource_class()
        original_filename = "name_{}.jpg".format(get_random_string(6))
        signal_fired = False

        def signal_handler(sender, instance, old_name, new_name, options, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is self.resource_class
            assert instance is resource

            assert old_name == instance.name
            assert new_name == "new name.png"

            # ensure instance filled
            assert instance.resource_name == helpers.get_filename(original_filename)
            assert instance.extension == helpers.get_extension(original_filename)
            assert instance.size == 9711423
            assert instance.checksum == "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"

            # extra parameters passed to `rename()`
            assert options == {
                "key1": "value1",
                "key2": "value2"
            }

        resource.attach(NASA_FILEPATH, name=original_filename)

        signals.pre_rename_file.connect(signal_handler)
        assert signal_fired is False
        resource.rename("new name.png", key1="value1", key2="value2")
        assert signal_fired is True
        signals.pre_rename_file.disconnect(signal_handler)

        resource.delete_file()

    def test_post_rename_file(self):
        resource = self.resource_class()
        original_filename = "name_{}.jpg".format(get_random_string(6))
        old_filename = ""
        signal_fired = False

        def signal_handler(sender, instance, old_name, new_name, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is self.resource_class
            assert instance is resource

            assert old_name == old_filename
            assert new_name == "new name.png"

            # ensure instance filled
            assert instance.resource_name == "new name"
            assert instance.extension == "png"
            assert instance.size == 9711423
            assert instance.checksum == "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"

            # extra parameters passed to `rename()`
            assert options == {
                "key1": "value1",
                "key2": "value2"
            }

            # result of `_rename()` method
            assert response == {
                "success": True,
            }

        resource.attach(NASA_FILEPATH, name=original_filename)
        old_filename = resource.name

        signals.post_rename_file.connect(signal_handler)
        assert signal_fired is False
        resource.rename("new name.png", key1="value1", key2="value2")
        assert signal_fired is True
        signals.post_rename_file.disconnect(signal_handler)

        resource.delete_file()

    def test_renaming_to_same_name_not_fires_signals(self):
        resource = self.resource_class()
        pre_signal_fired = False
        post_signal_fired = False

        def pre_signal_handler(sender, **kwargs):
            nonlocal pre_signal_fired
            pre_signal_fired = True

        def post_signal_handler(sender, **kwargs):
            nonlocal post_signal_fired
            post_signal_fired = True

        resource.attach(NASA_FILEPATH, name="name_{}.jpg".format(get_random_string(6)))

        original_name = resource.name
        original_resource_name = resource.resource_name

        signals.pre_rename_file.connect(pre_signal_handler)
        signals.post_rename_file.connect(post_signal_handler)
        assert pre_signal_fired is False
        assert post_signal_fired is False
        resource.rename(os.path.basename(original_name))
        assert pre_signal_fired is True
        assert post_signal_fired is True
        signals.pre_rename_file.disconnect(pre_signal_handler)
        signals.post_rename_file.disconnect(post_signal_handler)

        assert original_name == resource.name
        assert original_resource_name == resource.resource_name

        resource.delete_file()

    def test_pre_delete_file(self):
        resource = self.resource_class()
        signal_fired = False

        def signal_handler(sender, instance, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is self.resource_class
            assert instance is resource

        resource.attach(NASA_FILEPATH, name="name_{}.jpg".format(get_random_string(6)))

        signals.pre_delete_file.connect(signal_handler)
        assert signal_fired is False
        resource.delete_file()
        assert signal_fired is True
        signals.pre_delete_file.disconnect(signal_handler)

    def test_post_delete_file(self):
        resource = self.resource_class()
        signal_fired = False

        def signal_handler(sender, instance, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is self.resource_class
            assert instance is resource

            # extra parameters passed to `rename()`
            assert options == {
                "key1": "value1",
                "key2": "value2"
            }

            # result of `_delete_file` method
            assert response == {
                "success": True,
            }

        resource.attach(NASA_FILEPATH, name="name_{}.jpg".format(get_random_string(6)))

        signals.post_delete_file.connect(signal_handler)
        assert signal_fired is False
        resource.delete_file(key1="value1", key2="value2")
        assert signal_fired is True
        signals.post_delete_file.disconnect(signal_handler)


class TestFileFieldResource(TestFileResource):
    resource_class = DummyFileFieldResource
    resource_attachment = MEDITATION_FILEPATH
    resource_basename = "Meditation"
    resource_extension = "svg"
    resource_name = "file_field/Meditation{suffix}.svg"
    resource_size = 47193
    resource_checksum = "7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d"
    resource_mimetype = "image/svg+xml"
    resource_field_name = "file"

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.attach(cls.resource_attachment)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(5) == b'<?xml'

    def test_get_file_field(self, storage):
        assert (
            storage.resource.get_file_field()
            is storage.resource._meta.get_field(self.resource_field_name)
        )

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == os.path.dirname(self.resource_name)

    def test_get_file_storage(self, storage):
        assert storage.resource.get_file_storage() is default_storage

    def test_path(self, storage):
        assert utils.match_path(
            storage.resource.path,
            "/media/" + self.resource_name,
        )

    def test_url(self, storage):
        assert utils.match_path(
            storage.resource.url,
            "/media/" + self.resource_name,
        )

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "mimetype": self.resource_mimetype,
                "url": storage.resource.url,
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id"}
        )


class TestFileFieldResourceAttach(TestFileResourceAttach):
    resource_class = DummyFileFieldResource
    resource_attachment = DOCUMENT_FILEPATH
    resource_basename = "document"
    resource_extension = "pdf"
    resource_size = 3028
    resource_checksum = "93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e"
    resource_mimetype = "application/pdf"


class TestFileFieldResourceRename(TestFileResourceRename):
    resource_class = DummyFileFieldResource
    resource_attachment = AUDIO_FILEPATH
    resource_size = 2113939
    resource_checksum = "4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d"
    resource_mimetype = "audio/mpeg"
    old_name = "old_name_{}.mp3".format(get_random_string(6))
    new_name = "new_name_{}.wav".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
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

    def test_old_file_existence(self, storage):
        file_storage = storage.resource.get_file_storage()
        assert file_storage.exists(storage.old_resource_name) is True

    def test_new_file_existence(self, storage):
        file_storage = storage.resource.get_file_storage()
        assert file_storage.exists(storage.resource.name) is True


class TestFileFieldResourceDelete(TestFileResourceDelete):
    resource_class = DummyFileFieldResource
    resource_attachment = VIDEO_FILEPATH

    def test_file_existence(self, storage):
        file_storage = storage.resource.get_file_storage()
        assert file_storage.exists(storage.old_resource_name) is False

    def test_file_field_empty(self, storage):
        assert storage.resource.get_file().name is None


class TestFileFieldResourceEmpty(TestEmptyFileResource):
    resource_class = DummyFileFieldResource

    def test_as_dict(self, storage):
        with pytest.raises(ValueError):
            storage.resource.as_dict()

    def test_name(self, storage):
        with pytest.raises(ValueError):
            storage.resource.name

    def test_get_file_size(self, storage):
        with pytest.raises(ValueError):
            storage.resource.get_file_size()

    def test_open(self, storage):
        with pytest.raises(ValueError):
            storage.resource.open()

    def test_rename_file(self, storage):
        with pytest.raises(ValueError):
            storage.resource.rename("bla-bla.jpg")

    def test_delete_file(self, storage):
        storage.resource.delete_file()

    def test_path(self, storage):
        with pytest.raises(ValueError):
            storage.resource.path

    def test_url(self, storage):
        with pytest.raises(ValueError):
            storage.resource.url


class TestImageFieldResource(TestFileFieldResource):
    resource_class = DummyImageFieldResource
    resource_attachment = NASA_FILEPATH
    resource_basename = "milky-way-nasa"
    resource_extension = "jpg"
    resource_name = "image_field/milky-way-nasa{suffix}.jpg"
    resource_size = 9711423
    resource_checksum = "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"
    resource_mimetype = "image/jpeg"
    resource_field_name = "image"

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            title="Nasa",
            description="Calliphora is a genus of blow flies, also known as bottle flies",
        )
        storage.resource.attach(cls.resource_attachment)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "mimetype": self.resource_mimetype,
                "width": 3501,
                "height": 2525,
                "cropregion": "",
                "title": "Nasa",
                "description": "Calliphora is a genus of blow flies, also known as bottle flies",
                "url": storage.resource.url,
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id"}
        )

    def test_read(self, storage):
        with storage.resource.open("rb") as fp:
            assert fp.read(5) == b'\xff\xd8\xff\xe0\x00'

    def test_title(self, storage):
        assert storage.resource.title == "Nasa"

    def test_description(self, storage):
        assert storage.resource.description == "Calliphora is a genus of blow flies, " \
                                               "also known as bottle flies"

    def test_width(self, storage):
        assert storage.resource.width == 3501

    def test_height(self, storage):
        assert storage.resource.height == 2525

    def test_ratio(self, storage):
        assert storage.resource.ratio == Decimal("1.38653465")

    def test_hw_ratio(self, storage):
        assert storage.resource.hw_ratio == Decimal("0.72122251")

    def test_prepare_file(self, storage):
        obj = DummyImageFieldResource()
        with open(CALLIPHORA_FILEPATH, "rb") as fp:
            file = File(fp)
            assert obj._prepare_file(file) is file
            assert obj.width == 804
            assert obj.height == 1198

    def test_filtered_invalid_file(self, storage):
        obj = self.resource_class()
        with pytest.raises(UnsupportedResource):
            with open(MEDITATION_FILEPATH, "rb") as fp:
                obj._prepare_file(File(fp))


class TestImageFieldResourceAttach(TestFileFieldResourceAttach):
    resource_class = DummyImageFieldResource
    resource_attachment = FIRE_BREATHING_FILEPATH
    resource_basename = "Fire breathing"
    resource_extension = "webp"
    resource_size = 82698
    resource_checksum = "033e550230bdac841d5443d1c3e063e975a78cdbd4e04416c6583b43eaeede4e"
    resource_mimetype = "image/webp"

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


class TestImageFieldResourceRename(TestFileFieldResourceRename):
    resource_class = DummyImageFieldResource
    resource_attachment = CALLIPHORA_FILEPATH
    resource_size = 254766
    resource_checksum = "d4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386"
    resource_mimetype = "image/jpeg"
    old_name = "old_name_{}.txt".format(get_random_string(6))
    new_name = "new_name_{}.log".format(get_random_string(6))


class TestImageFieldResourceDelete(TestFileFieldResourceDelete):
    resource_class = DummyImageFieldResource
    resource_attachment = NATURE_FILEPATH


class TestImageFieldResourceEmpty(TestFileFieldResourceEmpty):
    resource_class = DummyFileFieldResource


class TestVersatileImageResource(TestImageFieldResource):
    resource_class = DummyVersatileImageResource
    resource_attachment = FIRE_BREATHING_FILEPATH
    resource_basename = "Fire breathing"
    resource_extension = "webp"
    resource_name = "versatile_image_field/Fire_breathing{suffix}.webp"
    resource_size = 82698
    resource_checksum = "033e550230bdac841d5443d1c3e063e975a78cdbd4e04416c6583b43eaeede4e"
    resource_mimetype = "image/webp"
    resource_field_name = "image"

    def test_width(self, storage):
        assert storage.resource.width == 1024

    def test_height(self, storage):
        assert storage.resource.height == 752

    def test_ratio(self, storage):
        assert storage.resource.ratio == Decimal("1.36170213")

    def test_hw_ratio(self, storage):
        assert storage.resource.hw_ratio == Decimal("0.734375")

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "mimetype": self.resource_mimetype,
                "width": 1024,
                "height": 752,
                "cropregion": "",
                "title": "Nasa",
                "description": "Calliphora is a genus of blow flies, also known as bottle flies",
                "url": storage.resource.url,
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id"}
        )

    def test_read(self, storage):
        with storage.resource.open("rb") as fp:
            assert fp.read(5) == b'RIFF\x02'

    def test_get_variations(self, storage):
        variations = storage.resource.get_variations()
        assert len(variations) == 3
        assert set(variations.keys()) == {"desktop", "mobile", "square"}
        assert all(isinstance(v, PaperVariation) for v in variations.values()) is True

    def test_get_variation_file(self, storage):
        vfile = storage.resource.get_variation_file("desktop")
        assert isinstance(vfile, VariationFile)
        assert vfile.exists() is True

        file_path = list(os.path.splitext(self.resource_name))
        file_path.insert(-1, ".desktop")
        assert utils.match_path(
            vfile.path,
            "/media/" + "".join(file_path)
        )

    def test_get_non_existed_variation_file(self, storage):
        with pytest.raises(KeyError):
            storage.resource.get_variation_file("something")

    def test_variation_files(self, storage):
        assert dict(storage.resource.variation_files()) == {
            "desktop": storage.resource.desktop,
            "mobile": storage.resource.mobile,
            "square": storage.resource.square,
        }

    def test_variation_attribute(self, storage):
        assert isinstance(storage.resource.desktop, VariationFile)
        assert isinstance(storage.resource.mobile, VariationFile)

    def test_missing_variation_attribute(self, storage):
        with pytest.raises(AttributeError):
            storage.resource.tablet  # noqa

    def test_variation_files_exists(self, storage):
        assert os.path.exists(storage.resource.path) is True
        assert os.path.exists(storage.resource.desktop.path) is True
        assert os.path.exists(storage.resource.mobile.path) is True

    def test_calculate_max_size(self, storage):
        assert storage.resource.calculate_max_size((3000, 2000)) == (900, 600)
        assert storage.resource.calculate_max_size((2000, 3000)) == (800, 1200)


class TestVersatileImageAttach(TestImageFieldResourceAttach):
    resource_class = DummyVersatileImageResource
    resource_attachment = CALLIPHORA_FILEPATH
    resource_basename = "calliphora"
    resource_extension = "jpg"
    resource_size = 254766
    resource_checksum = "d4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386"
    resource_mimetype = "image/jpeg"

    def test_need_recut(self):
        with self.get_resource() as resource:
            with open(self.resource_attachment, "rb") as fp:
                resource.attach(fp)

            assert resource.need_recut is True


class TestVersatileImageRename(TestImageFieldResourceRename):
    resource_class = DummyVersatileImageResource
    resource_attachment = FIRE_BREATHING_FILEPATH
    resource_size = 82698
    resource_checksum = "033e550230bdac841d5443d1c3e063e975a78cdbd4e04416c6583b43eaeede4e"
    resource_mimetype = "image/webp"
    old_name = "old_name_{}.webp".format(get_random_string(6))
    new_name = "new_name_{}.jpg".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name
        storage.old_resource_path = storage.resource.path
        storage.old_resource_desktop_path = storage.resource.desktop.path
        storage.old_resource_mobile_path = storage.resource.mobile.path
        storage.old_resource_square_path = storage.resource.square.path

        storage.resource.rename(cls.new_name)
        yield

        os.unlink(storage.old_resource_path)
        os.unlink(storage.old_resource_desktop_path)
        os.unlink(storage.old_resource_mobile_path)
        os.unlink(storage.old_resource_square_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestVersatileImageDelete(TestImageFieldResourceDelete):
    resource_class = DummyVersatileImageResource
    resource_attachment = NASA_FILEPATH


class TestVersatileImageEmpty(TestImageFieldResourceEmpty):
    resource_class = DummyVersatileImageResource

    def test_variation_files(self, storage):
        assert list(storage.resource.variation_files()) == []

    def test_missing_variation_attribute(self, storage):
        with pytest.raises(AttributeError):
            storage.resource.tablet  # noqa


@pytest.mark.django_db
class TestVariations:
    resource_class = DummyVersatileImageResource

    def test_delete_variations(self):
        resource = self.resource_class()
        resource.attach(NASA_FILEPATH)
        resource.save()

        assert os.path.exists(resource.path) is True
        assert os.path.exists(resource.desktop.path) is True
        assert os.path.exists(resource.mobile.path) is True
        assert os.path.exists(resource.square.path) is True

        resource.delete_variations()
        assert os.path.exists(resource.path) is True
        assert os.path.exists(resource.desktop.path) is False
        assert os.path.exists(resource.mobile.path) is False
        assert os.path.exists(resource.square.path) is False

        resource.delete_file()
        resource.delete()

    def test_delete_file(self):
        resource = self.resource_class()
        resource.attach(NASA_FILEPATH)
        resource.save()

        assert os.path.exists(resource.path) is True
        assert os.path.exists(resource.desktop.path) is True
        assert os.path.exists(resource.mobile.path) is True
        assert os.path.exists(resource.square.path) is True

        resource.delete_file()

        with pytest.raises(ValueError):
            resource.path

        with pytest.raises(ValueError):
            resource.desktop.path

        with pytest.raises(ValueError):
            resource.mobile.path

        with pytest.raises(ValueError):
            resource.square.path

        resource.delete()

    def test_reattach_file(self):
        resource = self.resource_class()
        resource.attach(CALLIPHORA_FILEPATH, name="initial.jpg")

        assert utils.match_path(
            resource.desktop.name,
            "{}/initial{{suffix}}.desktop.jpg".format(
                resource.get_file_folder()
            )
        )

        # check `variation_files()` cache
        assert not hasattr(resource, "_variation_files_cache")
        resource.variation_files()
        assert resource._variation_files_cache == tuple([
            ("desktop", resource.desktop),
            ("mobile", resource.mobile),
            ("square", resource.square),
        ])

        os.remove(resource.path)
        resource.attach(NATURE_FILEPATH, name="reattached.jpg")

        assert utils.match_path(
            resource.desktop.name,
            "{}/reattached{{suffix}}.desktop.jpg".format(
                resource.get_file_folder()
            )
        )

        # check `variation_files()` cache
        assert not hasattr(resource, "_variation_files_cache")
        resource.variation_files()
        assert resource._variation_files_cache == tuple([
            ("desktop", resource.desktop),
            ("mobile", resource.mobile),
            ("square", resource.square),
        ])

        resource.delete_file()

    def test_recut(self):
        resource = self.resource_class()
        resource.attach(NATURE_FILEPATH)
        resource.save()

        resource.delete_variations()

        assert os.path.exists(resource.path) is True
        assert os.path.exists(resource.desktop.path) is False
        assert os.path.exists(resource.mobile.path) is False
        assert os.path.exists(resource.square.path) is False

        resource.recut(["mobile", "square"])

        assert os.path.exists(resource.path) is True
        assert os.path.exists(resource.desktop.path) is False
        assert os.path.exists(resource.mobile.path) is True
        assert os.path.exists(resource.square.path) is True

        resource.delete_file()
        resource.delete()

    def test_variation_created_signal(self):
        resource = self.resource_class()
        resource.attach(NATURE_FILEPATH)

        signal_fired_times = 0
        signals_fired = {
            "desktop": False,
            "mobile": False,
            "square": False,
        }

        def signal_handler(sender, instance, name, **kwargs):
            nonlocal signal_fired_times
            nonlocal signals_fired
            signal_fired_times += 1
            signals_fired[name] = True
            assert sender is self.resource_class
            assert instance is resource

        signals.variation_created.connect(signal_handler)
        resource.save()
        signals.variation_created.disconnect(signal_handler)

        assert signal_fired_times == 3
        assert signals_fired == {
            "desktop": True,
            "mobile": True,
            "square": True,
        }

        resource.delete_file()
        resource.delete()
