import os

import pytest
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
        storage.file = CloudinaryFieldFile(storage.resource)
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
        resource = CloudinaryResource(storage.resource.public_id)
        file = CloudinaryFieldFile(resource, type=self.type, resource_type=self.resource_type)

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

    def test_size(self, storage):
        assert storage.file.size == self.resource_size

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

    def test_format(self, storage):
        assert storage.file.format is None

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(storage.resource.public_id)
        file = CloudinaryFieldFile(resource, type=self.type, resource_type=self.resource_type)
        assert file.format is None

    def test_open(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b'%PDF'

    def test_open_text(self, storage):
        with storage.file.open('r') as fp:
            assert fp.read(4) == '%PDF'

    def test_closed(self, storage):
        assert storage.file.closed is True
        with storage.file.open():
            assert storage.file.closed is False
        assert storage.file.closed is True


class TestCloudinaryImage(TestCloudinaryFieldFile):
    resource_type = 'image'
    upload_file = NATURE_FILEPATH
    resource_name = 'Nature_Tree'
    resource_ext = ''  # no extension for image
    resource_size = 672759

    def test_format(self, storage):
        assert storage.file.format == 'jpg'

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(storage.resource.public_id)
        file = CloudinaryFieldFile(resource, type=self.type, resource_type=self.resource_type)
        assert file.format == 'jpg'

    def test_open(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b'\xff\xd8\xff\xe0'

    def test_open_text(self, storage):
        with storage.file.open('r') as fp:
            with pytest.raises(UnicodeDecodeError):
                fp.read(4)


class TestCloudinaryMedia(TestCloudinaryFieldFile):
    resource_type = 'video'
    upload_file = AUDIO_FILEPATH
    resource_name = 'audio'
    resource_ext = ''  # no extension for media
    resource_size = 2113939

    def test_format(self, storage):
        assert storage.file.format == 'mp3'

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(storage.resource.public_id)
        file = CloudinaryFieldFile(resource, type=self.type, resource_type=self.resource_type)
        assert file.format == 'mp3'

    def test_open(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b'ID3\x03'

    def test_open_text(self, storage):
        with storage.file.open('r') as fp:
            assert fp.read(3) == 'ID3'


class CloudinaryFileResource(TestFileResource):
    def test_type(self, storage):
        raise NotImplementedError

    def test_public_id(self, storage):
        raise NotImplementedError

    def test_get_file_field(self, storage):
        assert (
            storage.resource.get_file_field()
            == storage.resource._meta.get_field(self.file_field_name)  # noqa: F821
        )

    def test_get_file_name(self, storage):
        raise NotImplementedError

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url.startswith('https://res.cloudinary.com/')

    def test_url(self, storage):
        assert storage.resource.url.startswith('https://res.cloudinary.com/')

    def test_closed(self, storage):
        with storage.resource.open():
            assert storage.resource.closed is False
        assert storage.resource.closed is True

    def test_seekable(self, storage):
        with storage.resource.open() as fp:
            assert fp.seekable() is True

    def test_readable(self, storage):
        with storage.resource.open() as fp:
            assert fp.readable() is True

    def test_writable(self, storage):
        with storage.resource.open() as fp:
            assert fp.writable() is False

    def test_open(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'\xff\xd8\xff\xe0'

    def test_close(self, storage):
        fp = storage.resource.open()
        assert storage.resource.closed is False
        fp.close()
        assert storage.resource.closed is True

    def test_seek(self, storage):
        with storage.resource.open() as fp:
            if fp.seekable():
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
