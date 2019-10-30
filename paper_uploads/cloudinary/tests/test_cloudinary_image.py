import re
import pytest
from pathlib import Path
from django.core.files import File
from tests.app.models import Page
from ... import validators
from ..models import CloudinaryImage, CloudinaryImageField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryImage:
    def test_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = CloudinaryImage(
                alt='Alternate text',
                title='Image title',
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_image'
            )
            obj.attach_file(File(jpeg_file, name='Image.Jpeg'))
            obj.save()

        try:
            assert obj.PROXY_FILE_ATTRIBUTES == {'url'}
            assert obj.cloudinary_resource_type == 'image'
            assert obj.cloudinary_type == 'upload'
            assert obj.file.resource_type == 'image'
            assert obj.file.type == 'upload'

            assert obj.name == 'Image'
            assert obj.canonical_name == 'Image.jpg'
            assert obj.extension == 'jpg'
            assert obj.size == 214779
            assert obj.hash == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert obj.alt == 'Alternate text'
            assert obj.title == 'Image title'
            assert obj.width == 1600
            assert obj.height == 1200
            assert obj.cropregion == ''

            for name in obj.PROXY_FILE_ATTRIBUTES:
                assert getattr(obj, name) == getattr(obj.file, name)

            # SlaveModelMixin methods
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('cloud_image')
            assert obj.get_validation() == {
                'acceptFiles': ['image/*']
            }

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+', obj.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.jpg', obj.get_file_name()) is not None
            assert obj.get_file_size() == 214779
            assert obj.file_exists() is True
            assert obj.get_file_hash() == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/image/upload/[^/]+/Image_\w+\.jpg', obj.get_file_url()) is not None
        finally:
            obj.delete()

        assert obj.file_exists() is False

    def test_orphan_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = CloudinaryImage()
            obj.attach_file(File(jpeg_file, name='Image.Jpeg'))
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete()

        assert obj.file_exists() is False


class TestCloudinaryImageField:
    def test_rel(self):
        field = CloudinaryImageField()
        assert field.null is True
        assert field.related_model == 'paper_uploads_cloudinary.CloudinaryImage'

    def test_validators(self):
        field = CloudinaryImageField(validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
        ])
        field.contribute_to_class(Page, 'cloud_image')

        assert field.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ['image/*']
        }

    def test_cloudinary_options(self):
        field = CloudinaryImageField(public_id='myimage', folder='images')
        assert field.cloudinary_options == {
            'use_filename': True,
            'unique_filename': True,
            'overwrite': True,
            'public_id': 'myimage',
            'folder': 'images',
        }
