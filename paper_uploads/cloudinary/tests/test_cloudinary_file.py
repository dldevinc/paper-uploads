import re
import pytest
from pathlib import Path
from django.core.files import File
from tests.app.models import Page
from ... import validators
from ..models import CloudinaryFile, CloudinaryFileField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryFile:
    def test_file(self):
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            obj = CloudinaryFile(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file'
            )
            obj.attach_file(File(pdf_file, name='Doc.PDF'))
            obj.save()

        try:
            assert obj.PROXY_FILE_ATTRIBUTES == {'url'}
            assert obj.cloudinary_resource_type == 'raw'
            assert obj.cloudinary_type == 'upload'
            assert obj.file.resource_type == 'raw'
            assert obj.file.type == 'upload'

            assert obj.name == 'Doc'
            assert obj.display_name == 'Doc'
            assert obj.canonical_name == 'Doc.pdf'
            assert obj.extension == 'pdf'
            assert obj.size == 9678
            assert obj.hash == 'bebc2ddd2a8b8270b359990580ff346d14c021fa'

            for name in obj.PROXY_FILE_ATTRIBUTES:
                assert getattr(obj, name) == getattr(obj.file, name)

            # SlaveModelMixin methods
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('cloud_file')
            assert obj.get_validation() == {}

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+\.PDF', obj.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.PDF', obj.get_file_name()) is not None
            assert obj.get_file_size() == 9678
            assert obj.file_exists() is True
            assert obj.get_file_hash() == 'bebc2ddd2a8b8270b359990580ff346d14c021fa'
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/raw/upload/[^/]+/Doc_\w+\.PDF', obj.get_file_url()) is not None
        finally:
            obj.delete()

        assert obj.file_exists() is False

    def test_orphan_file(self):
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            obj = CloudinaryFile()
            obj.attach_file(File(pdf_file, name='Doc.PDF'))
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete()

        assert obj.file_exists() is False


class TestCloudinaryFileField:
    def test_rel(self):
        field = CloudinaryFileField()
        assert field.null is True
        assert field.related_model == 'paper_uploads_cloudinary.CloudinaryFile'

    def test_validators(self):
        field = CloudinaryFileField(validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
        ])
        field.contribute_to_class(Page, 'cloud_file')

        assert field.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg')
        }

    def test_cloudinary_options(self):
        field = CloudinaryFileField(public_id='myfile', folder='files')
        assert field.cloudinary_options == {
            'use_filename': True,
            'unique_filename': True,
            'overwrite': True,
            'public_id': 'myfile',
            'folder': 'files',
        }
