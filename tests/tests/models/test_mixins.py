import tempfile
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import FieldDoesNotExist
from django.core.files import File

from examples.fields.standard.models import Page

from paper_uploads.models.mixins import (
    BacklinkModelMixin,
    FileProxyMixin,
)

from ..mixins import FileProxyTestMixin


class DummyFileProxyMixin(FileProxyMixin):
    def __init__(self):
        super().__init__()
        with tempfile.NamedTemporaryFile("w", delete=False) as tfile:
            tfile.write("Hello, world!")

        self.name = tfile.name

    def get_file(self) -> File:
        return File(None, name=self.name)

    def _require_file(self):
        pass


class TestBacklinkModelMixin:
    owner_model = None
    owner_fieldname = "field"

    def test_set_owner_field(self):
        mock = MagicMock(spec=BacklinkModelMixin)
        BacklinkModelMixin.set_owner_field(mock, Page, "file")
        assert mock.owner_app_label == "standard_fields"
        assert mock.owner_model_name == "page"
        assert mock.owner_fieldname == "file"

    def test_set_non_existent_field(self):
        mock = MagicMock(spec=BacklinkModelMixin)
        with pytest.raises(FieldDoesNotExist):
            BacklinkModelMixin.set_owner_field(mock, Page, "non_existent_method")

    def test_get_owner_model(self):
        mock = MagicMock(spec=BacklinkModelMixin)
        mock.owner_app_label = "standard_fields"
        mock.owner_model_name = "page"
        model = BacklinkModelMixin.get_owner_model(mock)
        assert model is Page

    def test_get_owner_field(self):
        mock = MagicMock(spec=BacklinkModelMixin)
        mock.owner_fieldname = "file"
        mock.get_owner_model.return_value = Page
        field = BacklinkModelMixin.get_owner_field(mock)
        assert field is Page._meta.get_field("file")

    def test_uncomplete_data(self):
        # No data at all
        mock = MagicMock(spec=BacklinkModelMixin)
        mock.owner_app_label = ""
        mock.owner_model_name = ""
        mock.owner_fieldname = ""
        assert BacklinkModelMixin.get_owner_model(mock) is None

        mock.get_owner_model.return_value = Page
        assert BacklinkModelMixin.get_owner_field(mock) is None

        # app name only
        mock = MagicMock(spec=BacklinkModelMixin)
        mock.owner_app_label = "standard_fields"
        mock.owner_model_name = ""
        mock.owner_fieldname = ""
        assert BacklinkModelMixin.get_owner_model(mock) is None

        mock.get_owner_model.return_value = Page
        assert BacklinkModelMixin.get_owner_field(mock) is None

        # model name only
        mock = MagicMock(spec=BacklinkModelMixin)
        mock.owner_app_label = ""
        mock.owner_model_name = "page"
        mock.owner_fieldname = ""
        assert BacklinkModelMixin.get_owner_model(mock) is None

        mock.get_owner_model.return_value = Page
        assert BacklinkModelMixin.get_owner_field(mock) is None

        # app and model names only
        mock = MagicMock(spec=BacklinkModelMixin)
        mock.owner_app_label = "standard_fields"
        mock.owner_model_name = "page"
        mock.owner_fieldname = ""
        mock.get_owner_model.return_value = Page
        assert BacklinkModelMixin.get_owner_field(mock) is None

    def test_get_non_existent_field(self):
        mock = MagicMock(spec=BacklinkModelMixin)
        mock.owner_app_label = "standard_fields"
        mock.owner_model_name = "page"
        mock.owner_fieldname = "non_existent_field"
        mock.get_owner_model.return_value = Page
        assert BacklinkModelMixin.get_owner_field(mock) is None


class TestFileProxyMixin(FileProxyTestMixin):
    resource_size = 13

    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyFileProxyMixin()
        yield

    def test_read(self, storage):
        with storage.resource.open("r") as fp:
            assert fp.read(5) == "Hello"

    def test_writable(self, storage):
        # Режим "w" стирает содержимое, что влияет на другие тесты
        with storage.resource.open("a") as fp:
            assert fp.writable() is True

    def test_multiple_chunks(self, storage, chunk_size=1024):
        return super().test_multiple_chunks(storage, chunk_size=4)

    def test_close_cleans_private_field(self, storage):
        with storage.resource:
            assert storage.resource._get_file() is not None
        assert storage.resource._get_file() is None

    def test_reopen_uses_same_object(self, storage):
        with storage.resource.open("r") as fp:
            with storage.resource.open("r") as fp2:
                assert fp is fp2

    @patch("django.core.files.File.seekable", return_value=False)
    def test_reopen_non_seekable(self, mock, storage):
        with storage.resource.open("r") as fp:
            with storage.resource.open("r") as fp2:
                assert fp is not fp2
                assert fp.closed
                assert fp2.closed is False

    def test_reopen_with_other_mode(self, storage):
        with storage.resource.open("r") as fp:
            with storage.resource.open("rb") as fp2:
                assert fp is not fp2
                assert fp.closed
                assert fp2.closed is False
