import re
import pytest
from pathlib import Path
from django.core.files import File
from tests.app.models import Page
from ..models import CloudinaryFile

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryFile:
    def test_file(self):
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            object = CloudinaryFile(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file'
            )
            object.attach_file(File(fp, name='Doc.PDF'))
            object.save()

        try:
            assert object.PROXY_FILE_ATTRIBUTES == {'url'}
            assert object.cloudinary_resource_type == 'raw'
            assert object.cloudinary_type == 'upload'
            assert object.file.resource_type == 'raw'
            assert object.file.type == 'upload'

            assert object.name == 'Doc'
            assert object.display_name == 'Doc'
            assert object.canonical_name == 'Doc.pdf'
            assert object.extension == 'pdf'
            assert object.size == 9678
            assert object.hash == 'bebc2ddd2a8b8270b359990580ff346d14c021fa'

            # SlaveModelMixin methods
            assert object.get_owner_model() is Page
            assert object.get_owner_field() is Page._meta.get_field('cloud_file')
            assert object.get_validation() == {}

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+\.PDF', object.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.PDF', object.get_file_name()) is not None
            assert object.get_file_size() == 9678
            assert object.file_exists() is True
            assert object.get_file_hash() == 'bebc2ddd2a8b8270b359990580ff346d14c021fa'
            assert re.fullmatch(r'http://res.cloudinary.com/[^/]+/raw/upload/[^/]+/Doc_\w+.PDF', object.get_file_url()) is not None

            for name in object.PROXY_FILE_ATTRIBUTES:
                assert getattr(object, name) == getattr(object.file, name)
        finally:
            object.delete()

        assert object.file_exists() is False

    def test_orphan_file(self):
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            object = CloudinaryFile()
            object.attach_file(File(fp, name='Doc.PDF'))
            object.save()

        try:
            assert object.get_owner_model() is None
            assert object.get_owner_field() is None
        finally:
            object.delete()

        assert object.file_exists() is False
