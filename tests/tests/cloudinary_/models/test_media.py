import posixpath
from contextlib import contextmanager
from pathlib import Path

import cloudinary.exceptions
import pytest
from cloudinary import uploader
from django.core.files import File
from django.utils.crypto import get_random_string

from app.models import CloudinaryMediaExample
from paper_uploads import exceptions
from paper_uploads.cloudinary.models import CloudinaryMedia

from ... import utils
from ...dummy import *
from ...models.test_dummy import (
    BacklinkModelMixin,
    TestFileFieldResourceAttach,
    TestFileFieldResourceDelete,
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
)
from .test_base import CloudinaryFileResource


class TestCloudinaryMedia(BacklinkModelMixin, CloudinaryFileResource):
    resource_url = '/media/files/%Y-%m-%d'
    resource_location = 'files/%Y-%m-%d'
    resource_name = 'audio'
    resource_extension = 'mp3'
    resource_size = 2113939
    resource_checksum = '4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d'
    owner_app_label = 'app'
    owner_model_name = 'cloudinarymediaexample'
    owner_fieldname = 'media'
    owner_model = CloudinaryMediaExample
    file_field_name = 'file'

    @classmethod
    def init_class(cls, storage):
        storage.resource = CloudinaryMedia(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        with open(AUDIO_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == 'private'
        assert file_field.resource_type == 'video'

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        pattern = posixpath.join(self.resource_location, 'audio{suffix}')
        assert public_id == utils.get_target_filepath(pattern, public_id)

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'audio{suffix}')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'caption': '{}.{}'.format(
                self.resource_name,
                self.resource_extension
            ),
            'size': self.resource_size,
            'file_info': '(mp3, 2.1\xa0MB)',
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'ID3\x03'

    def test_build_url(self, storage):
        url = storage.resource.build_url(audio_frequency="44100")
        assert url.startswith('https://res.cloudinary.com/')
        assert "/af_44100/" in url


class TestCloudinaryMediaAttach(TestFileFieldResourceAttach):
    resource_class = CloudinaryMedia
    resource_size = 2113939
    resource_checksum = '4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d'

    @contextmanager
    def get_resource(self):
        resource = self.resource_class()
        try:
            yield resource
        finally:
            resource.delete_file()

    def test_file_as_string(self):
        with self.get_resource() as resource:
            resource.attach(AUDIO_FILEPATH)

            assert resource.basename == "audio"
            assert resource.extension == "mp3"
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_file_as_path(self):
        with self.get_resource() as resource:
            resource.attach(Path(AUDIO_FILEPATH))

            assert resource.basename == "audio"
            assert resource.extension == "mp3"
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_file(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp)

            assert resource.basename == 'audio'
            assert resource.extension == 'mp3'
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_django_file(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                file = File(fp, name='audio.ogg')
                resource.attach(file)

            assert resource.basename == 'audio'
            assert resource.extension == 'mp3'
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_django_file_with_relative_path(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, "rb") as fp:
                file = File(fp, name="audios/audio.ogg")
                resource.attach(file)

            assert "/audios/" not in resource.name
            assert resource.basename == "audio"
            assert resource.extension == "mp3"
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_override_name(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp, name='overwritten.ogg')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'mp3'

    def test_override_name_with_relative_path(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, "rb") as fp:
                resource.attach(fp, name="audios/overwritten.mp3")

            assert "/audios/" not in resource.name
            assert resource.basename == "overwritten"
            assert resource.extension == "mp3"

    def test_override_django_name(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                file = File(fp, name='not_used.ogg')
                resource.attach(file, name='overwritten.mp3')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'mp3'

    def test_override_django_name_with_relative_path(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, "rb") as fp:
                file = File(fp, name="audios/not_used.png")
                resource.attach(file, name="overwritten.ogg")

            assert "/audios/" not in resource.name
            assert resource.basename == "overwritten"
            assert resource.extension == "mp3"

    def test_wrong_extension(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp, name='overwritten.gif')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'mp3'

    def test_file_position_at_end(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp)
                assert fp.tell() == self.resource_size

    def test_unsupported_file(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                with pytest.raises(exceptions.UnsupportedResource):
                    resource.attach(fp)


class TestCloudinaryMediaRename(BacklinkModelMixin, TestFileFieldResourceRename):
    resource_class = CloudinaryMedia
    resource_location = 'files/%Y-%m-%d'
    owner_app_label = 'app'
    owner_model_name = 'cloudinarymediaexample'
    owner_fieldname = 'media'
    owner_model = CloudinaryMediaExample

    @classmethod
    def init_class(cls, storage):
        storage.uid = get_random_string(5)
        storage.resource = cls.resource_class(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        with open(AUDIO_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_media_name_{}.mp3'.format(storage.uid))
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name

        storage.resource.rename('new_media_name_{}.ogg'.format(storage.uid))

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_exists(self, storage):
        file = storage.resource.get_file()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_source_name,
                type=file.resource.type,
                resource_type=file.resource.resource_type
            )

    def test_new_file_exists(self, storage):
        file = storage.resource.get_file()
        uploader.explicit(
            file.name,
            type=file.resource.type,
            resource_type=file.resource.resource_type
        )

    def test_old_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_media_name_{}{{suffix}}'.format(storage.uid)),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_media_name_{}{{suffix}}'.format(storage.uid)),
            file.name
        )

    def test_basename(self, storage):
        assert storage.resource.basename == utils.get_target_filepath(
            'new_media_name_{}{{suffix}}'.format(storage.uid),
            storage.resource.basename
        )

    def test_extension(self, storage):
        assert storage.resource.extension == 'mp3'


class TestCloudinaryMediaDelete(BacklinkModelMixin, TestFileFieldResourceDelete):
    resource_class = CloudinaryMedia
    resource_location = 'files/%Y-%m-%d'
    owner_app_label = 'app'
    owner_model_name = 'cloudinarymediaexample'
    owner_fieldname = 'media'
    owner_model = CloudinaryMediaExample

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        with open(AUDIO_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.mp3')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}'),
            storage.old_source_name
        )

    def test_file_not_exists(self, storage):
        file_field = storage.resource.get_file_field()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_source_name,
                type=file_field.type,
                resource_type=file_field.resource_type
            )


class TestCloudinaryFileEmpty(TestFileFieldResourceEmpty):
    recource_class = CloudinaryMedia

    def test_path(self, storage):
        pass
