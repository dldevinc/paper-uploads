import re
import pytest
from pathlib import Path
from django.core.files import File
from tests.app.models import Page
from ..models import CloudinaryImage

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryImage:
    def test_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            object = CloudinaryImage(
                alt='Alternate text',
                title='Image title',
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_image'
            )
            object.attach_file(File(fp, name='Image.Jpeg'))
            object.save()

        try:
            assert object.PROXY_FILE_ATTRIBUTES == {'url'}
            assert object.cloudinary_resource_type == 'image'
            assert object.cloudinary_type == 'upload'
            assert object.file.resource_type == 'image'
            assert object.file.type == 'upload'

            assert object.name == 'Image'
            assert object.canonical_name == 'Image.jpg'
            assert object.extension == 'jpg'
            assert object.size == 214779
            assert object.hash == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert object.alt == 'Alternate text'
            assert object.title == 'Image title'
            assert object.width == 1600
            assert object.height == 1200
            assert object.cropregion == ''

            # SlaveModelMixin methods
            assert object.get_owner_model() is Page
            assert object.get_owner_field() is Page._meta.get_field('cloud_image')
            assert object.get_validation() == {
                'acceptFiles': ['image/*']
            }

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+', object.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.jpg', object.get_file_name()) is not None
            assert object.get_file_size() == 214779
            assert object.file_exists() is True
            assert object.get_file_hash() == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert re.fullmatch(r'http://res.cloudinary.com/[^/]+/image/upload/[^/]+/Image_\w+.jpg', object.get_file_url()) is not None

            for name in object.PROXY_FILE_ATTRIBUTES:
                assert getattr(object, name) == getattr(object.file, name)
        finally:
            object.delete()

        assert object.file_exists() is False

    def test_orphan_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            object = CloudinaryImage()
            object.attach_file(File(fp, name='Image.Jpeg'))
            object.save()

        try:
            assert object.get_owner_model() is None
            assert object.get_owner_field() is None
        finally:
            object.delete()

        assert object.file_exists() is False
