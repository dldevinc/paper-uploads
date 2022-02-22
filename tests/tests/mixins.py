import os
import math


class BacklinkModelTestMixin:
    """
    Тестирование значений полей модели-владельца в классах тестов, использующих ресурс.
    """

    owner_model = None
    owner_fieldname = "field"

    def test_owner_app_label(self, storage):
        assert storage.resource.owner_app_label == self.owner_model._meta.app_label

    def test_owner_model_name(self, storage):
        assert storage.resource.owner_model_name == self.owner_model._meta.model_name.lower()

    def test_owner_fieldname(self, storage):
        assert storage.resource.owner_fieldname == self.owner_fieldname


class FileProxyTestMixin:
    """
    Тестирование файловых методов в классах тестов, использующих ресурс.
    """

    def test_read(self, storage):
        raise NotImplementedError

    def test_writable(self, storage):
        raise NotImplementedError

    def test_seekable(self, storage):
        with storage.resource.open() as fp:
            assert fp.seekable() is True

    def test_readable(self, storage):
        with storage.resource.open("r") as fp:
            assert fp.readable() is True

    def test_closed(self, storage):
        with storage.resource.open():
            assert storage.resource.closed is False
        assert storage.resource.closed is True

    def test_reopen_resets_position(self, storage):
        with storage.resource.open() as fp:
            if fp.seekable():
                fp.seek(4)
            else:
                fp.read(4)

            assert fp.tell() == 4

            with storage.resource.open() as fp2:
                assert fp2.tell() == 0

    def test_repeatable_close(self, storage):
        with storage.resource.open():
            pass
        storage.resource.close()

    def test_seek_and_tell(self, storage):
        with storage.resource.open() as fp:
            fp.seek(0, os.SEEK_END)
            assert fp.tell() == self.resource_size

    def test_multiple_chunks(self, storage, chunk_size=1024):
        with storage.resource.open() as fp:
            assert fp.multiple_chunks(chunk_size) is True

    def test_chunks(self, storage, chunk_size=1024):
        total_chunks = math.ceil(self.resource_size / chunk_size)

        chunk_counter = 0
        with storage.resource.open() as fp:
            for chunk in fp.chunks(chunk_size):
                chunk_counter += 1
                assert len(chunk) <= chunk_size

        assert chunk_counter == total_chunks
