import os

from cloudinary import CloudinaryResource, uploader

from paper_uploads.cloudinary.models.base import CloudinaryFieldFile

from ... import utils
from ...dummy import *


class TestCloudinaryFieldFile:
    type = "private"
    resource_type = "raw"

    resource_attachment = EXCEL_FILEPATH
    resource_basename = "table"
    resource_extension = ".xls"
    resource_size = 8704
    resource_checksum = "c9c8ad905aa5142731b1e8ab34d5862f871627fa7ad8005264494c2489d2061e"

    @classmethod
    def init_class(cls, storage):
        with open(cls.resource_attachment, "rb") as fp:
            storage.resource = uploader.upload_resource(
                fp,
                type=cls.type,
                resource_type=cls.resource_type,
                folder="data/now",
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
        assert utils.match_path(
            storage.resource.public_id,
            "data/now/{}{{suffix}}{}".format(
                self.resource_basename,
                self.resource_extension
            ),
            source=storage.resource.public_id
        )

    def test_name(self, storage):
        assert utils.match_path(
            storage.file.name,
            "data/now/{}{{suffix}}{}".format(
                self.resource_basename,
                self.resource_extension
            ),
            source=storage.resource.public_id
        )

    def test_metadata(self, storage):
        meta = storage.file.metadata
        assert "asset_id" in meta
        assert "public_id" in meta
        assert "version" in meta
        assert "version_id" in meta
        assert "signature" in meta
        assert "resource_type" in meta
        assert "created_at" in meta
        assert "bytes" in meta
        assert "type" in meta
        assert "url" in meta
        assert "secure_url" in meta

    def test_uploaded_metadata(self, storage):
        resource = CloudinaryResource(
            storage.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        file = CloudinaryFieldFile(resource, checksum=self.resource_checksum)

        meta = file.metadata
        assert "asset_id" in meta
        assert "public_id" in meta
        assert "version" in meta
        assert "version_id" in meta
        assert "signature" in meta
        assert "resource_type" in meta
        assert "created_at" in meta
        assert "bytes" in meta
        assert "type" in meta
        assert "url" in meta
        assert "secure_url" in meta

    def test_url(self, storage):
        assert storage.file.url.startswith("https://res.cloudinary.com/")

        if self.resource_type == "raw":
            extension = self.resource_extension
        else:
            extension = "." + storage.file.metadata["format"]

        assert utils.match_path(
            storage.file.url,
            "data/now/{}{{suffix}}{}".format(
                self.resource_basename,
                extension
            ),
            source=storage.resource.public_id
        )

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
            assert fp.read(4) == b"\xd0\xcf\x11\xe0"

    def test_seek(self, storage):
        with storage.file.open() as fp:
            fp.seek(0, os.SEEK_END)
            assert fp.tell() == self.resource_size

    def test_tell(self, storage):
        with storage.file.open() as fp:
            assert fp.tell() == 0


class TestCloudinaryImage(TestCloudinaryFieldFile):
    resource_type = "image"
    resource_attachment = NATURE_FILEPATH
    resource_basename = "Nature_Tree"
    resource_extension = ""  # no extension for image
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"

    def test_format(self, storage):
        assert storage.file.format == "jpg"

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(
            storage.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        file = CloudinaryFieldFile(resource, checksum=self.resource_checksum)
        assert file.format == "jpg"

    def test_read(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b"\xff\xd8\xff\xe0"


class TestCloudinaryMedia(TestCloudinaryFieldFile):
    resource_type = "video"
    resource_attachment = AUDIO_FILEPATH
    resource_basename = "audio"
    resource_extension = ""  # no extension for media
    resource_size = 2113939
    resource_checksum = "4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d"

    def test_format(self, storage):
        assert storage.file.format == "mp3"

    def test_uploaded_format(self, storage):
        resource = CloudinaryResource(
            storage.resource.public_id,
            type=self.type,
            resource_type=self.resource_type
        )
        file = CloudinaryFieldFile(resource, checksum=self.resource_checksum)
        assert file.format == "mp3"

    def test_read(self, storage):
        with storage.file.open() as fp:
            assert fp.read(4) == b"ID3\x03"
