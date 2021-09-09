import os

from cloudinary import CloudinaryResource, uploader

from paper_uploads.cloudinary.models.base import CloudinaryFieldFile

from ... import utils
from ...dummy import *
from ...models.test_base import TestFileResource


class TestCloudinaryFieldFile:
    type = 'private'
    resource_type = 'raw'

    upload_file = DOCUMENT_FILEPATH
    resource_name = 'document'
    resource_ext = '.pdf'
    resource_size = 3028
    resource_checksum = '93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e'

    @classmethod
    def init_class(cls, storage):
        with open(cls.upload_file, 'rb') as fp:
            storage.resource = uploader.upload_resource(
                fp,
                type=cls.type,
                resource_type=cls.resource_type,
                folder='data/now',
                use_filename=True,
                unique_filename=True,
                overwrite=True
            )
        storage.file = CloudinaryFieldFile(storage.resource, checksum=cls.resource_checksum)
        yield
        uploader.destroy(
            storage.resource.public_id,
            type=cls.type,
            resource_type=cls.resource_type,
            invalidate=True
        )

    def test_public_id(self, storage):
        assert storage.resource.public_id == utils.get_target_filepath(
            'data/now/{name}{{suffix}}{ext}'.format(name=self.resource_name, ext=self.resource_ext),
            storage.resource.public_id
        )

    def test_name(self, storage):
        assert storage.file.name == utils.get_target_filepath(
            'data/now/{name}{{suffix}}{ext}'.format(name=self.resource_name, ext=self.resource_ext),
            storage.resource.public_id
        )

    def test_metadata(self, storage):
        meta = storage.file.metadata
        assert 'asset_id' in meta
        assert 'public_id' in meta
        assert 'version' in meta
        assert 'version_id' in meta
        assert 'signature' in meta
        assert 'resource_type' in meta
        assert 'created_at' in meta
        assert 'bytes' in meta
        assert 'type' in meta
        assert 'url' in meta
        assert 'secure_url' in meta

    def test_uploaded_metadata(self, storage):
        resource = CloudinaryResource(
            storage.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        file = CloudinaryFieldFile(resource, checksum=self.resource_checksum)

        meta = file.metadata
        assert 'asset_id' in meta
        assert 'public_id' in meta
        assert 'version' in meta
        assert 'version_id' in meta
        assert 'signature' in meta
        assert 'resource_type' in meta
        assert 'created_at' in meta
        assert 'bytes' in meta
        assert 'type' in meta
        assert 'url' in meta
        assert 'secure_url' in meta

    def test_url(self, storage):
        assert storage.file.url.startswith('https://res.cloudinary.com/')

        if self.resource_type == 'raw':
            ext = self.resource_ext
        else:
            ext = '.' + storage.file.metadata['format']

        assert storage.file.url.endswith(utils.get_target_filepath(
            '/data/now/{name}{{suffix}}{ext}'.format(name=self.resource_name, ext=ext),
            storage.resource.public_id
        ))

    def test_size(self, storage):
        assert storage.file.size == self.resource_size

    def test_format(self, storage):
        assert storage.file.format is None

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(
            storage.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        file = CloudinaryFieldFile(resource, checksum=self.resource_checksum)
        assert file.format is None

    def test_closed(self, storage):
        with storage.file.open():
            assert storage.file.closed is False
        assert storage.file.closed is True

    def test_open(self, storage):
        with storage.file.open() as fp:
            assert fp is storage.file
        assert storage.file.file is not None

    def test_read(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b'%PDF'

    def test_seek(self, storage):
        with storage.file.open() as fp:
            fp.seek(0, os.SEEK_END)
            assert fp.tell() == self.resource_size

    def test_tell(self, storage):
        with storage.file.open() as fp:
            assert fp.tell() == 0


class TestCloudinaryImage(TestCloudinaryFieldFile):
    resource_type = 'image'
    upload_file = NATURE_FILEPATH
    resource_name = 'Nature_Tree'
    resource_ext = ''  # no extension for image
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'

    def test_format(self, storage):
        assert storage.file.format == 'jpg'

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(
            storage.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        file = CloudinaryFieldFile(resource, checksum=self.resource_checksum)
        assert file.format == 'jpg'

    def test_read(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b'\xff\xd8\xff\xe0'


class TestCloudinaryMedia(TestCloudinaryFieldFile):
    resource_type = 'video'
    upload_file = AUDIO_FILEPATH
    resource_name = 'audio'
    resource_ext = ''  # no extension for media
    resource_size = 2113939
    resource_checksum = '4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d'

    def test_format(self, storage):
        assert storage.file.format == 'mp3'

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(
            storage.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        file = CloudinaryFieldFile(resource, checksum=self.resource_checksum)
        assert file.format == 'mp3'

    def test_read(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b'ID3\x03'


class CloudinaryFileResource(TestFileResource):
    def test_type(self, storage):
        raise NotImplementedError

    def test_public_id(self, storage):
        raise NotImplementedError

    def test_name(self, storage):
        raise NotImplementedError

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == ""

    def test_get_file_field(self, storage):
        assert (
            storage.resource.get_file_field()
            == storage.resource._meta.get_field(self.file_field_name)  # noqa: F821
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url.startswith('https://res.cloudinary.com/')

    def test_url(self, storage):
        assert storage.resource.url.startswith('https://res.cloudinary.com/')

    def test_closed(self, storage):
        with storage.resource.open():
            assert storage.resource.closed is False
        assert storage.resource.closed is True

    def test_open(self, storage):
        with storage.resource.open() as fp:
            assert fp is storage.resource

    def test_reopen(self, storage):
        with storage.resource.open() as opened:
            with storage.resource.open() as reopened:
                assert opened is reopened

    def test_reopen_reset_position(self, storage):
        with storage.resource.open():
            storage.resource.read(4)  # change file position
            assert storage.resource.tell() == 4

            with storage.resource.open():
                assert storage.resource.tell() == 0

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'\xff\xd8\xff\xe0'

    def test_close(self, storage):
        with storage.resource.open():
            assert storage.resource._FileProxyMixin__file is not None
        assert storage.resource._FileProxyMixin__file is None

    def test_reclose(self, storage):
        with storage.resource.open():
            pass
        return storage.resource.close()

    def test_seekable(self, storage):
        with storage.resource.open() as fp:
            assert fp.seekable() is True

    def test_readable(self, storage):
        with storage.resource.open() as fp:
            assert fp.readable() is True

    def test_writable(self, storage):
        with storage.resource.open() as fp:
            assert fp.writable() is False

    def test_seek(self, storage):
        with storage.resource.open() as fp:
            fp.seek(0, os.SEEK_END)
            assert fp.tell() == self.resource_size

    def test_tell(self, storage):
        with storage.resource.open() as fp:
            assert fp.tell() == 0

    def test_get_cloudinary_options(self, storage):
        options = storage.resource.get_cloudinary_options()
        folder = utils.get_target_filepath(self.resource_location, '')  # noqa: F821
        assert options == {
            'use_filename': True,
            'unique_filename': True,
            'overwrite': True,
            'invalidate': True,
            'folder': folder
        }
