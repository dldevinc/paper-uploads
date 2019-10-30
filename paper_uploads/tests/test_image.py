import re
import os
import pytest
from pathlib import Path
from django.core.files import File
from django.utils.timezone import now
from tests.app.models import Page
from .. import validators
from ..models import UploadedImage, ImageField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestUploadedImage:
    def test_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = UploadedImage(
                alt='Alternate text',
                title='Image title',
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='image_ext'
            )
            obj.attach_file(File(jpeg_file, name='Image.Jpeg'))
            obj.save()

        try:
            suffix = re.match(r'Image((?:_\w+)?)', os.path.basename(obj.file.name)).group(1)

            assert obj.PROXY_FILE_ATTRIBUTES == {'url', 'path', 'open', 'read', 'close', 'closed'}
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

            assert os.path.isfile(obj.path)

            for name in obj.PROXY_FILE_ATTRIBUTES:
                assert getattr(obj, name) == getattr(obj.file, name)

            # SlaveModelMixin methods
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('image_ext')
            assert obj.get_validation() == {
                'acceptFiles': ['image/*']
            }

            # FileFieldContainerMixin methods
            assert obj.get_file_name() == 'images/{}/Image{}.jpg'.format(now().strftime('%Y-%m-%d'), suffix)
            assert obj.get_file_size() == 214779
            assert obj.file_exists() is True
            assert obj.get_file_hash() == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert obj.get_file_url() == '/media/images/{}/Image{}.jpg'.format(now().strftime('%Y-%m-%d'), suffix)

            # variations
            variations = obj.get_variations()
            assert 'desktop' in variations
            assert 'tablet' in variations
            assert 'admin' in variations

            variation_files = dict(obj.get_variation_files())
            assert getattr(obj, 'desktop') is variation_files['desktop']
            assert getattr(obj, 'tablet') is variation_files['tablet']
            assert getattr(obj, 'admin') is variation_files['admin']

            with pytest.raises(KeyError):
                obj.get_variation_file('nonexist')

            assert {
                name: os.path.basename(file.name)
                for name, file in obj.get_variation_files()
            } == {
                'desktop': 'Image{}.desktop.jpg'.format(suffix),
                'tablet': 'Image{}.tablet.jpg'.format(suffix),
                'admin': 'Image{}.admin.jpg'.format(suffix),
            }

            # get_draft_size()
            expected = {
                (3000, 2000): (1600, 1067),
                (1400, 1200): (1600, 1200),
                (800, 600): (1600, 600),
            }
            for input_size, output_size in expected.items():
                assert obj.get_draft_size(input_size) == output_size
        finally:
            obj.delete()

        assert obj.file_exists() is False

    def test_orphan_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = UploadedImage()
            obj.attach_file(File(jpeg_file, name='Image.Jpeg'))
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete()

        assert obj.file_exists() is False


class TestImageField:
    def test_rel(self):
        field = ImageField()
        assert field.null is True
        assert field.related_model == 'paper_uploads.UploadedImage'

    def test_validators(self):
        field = ImageField(validators=[
            validators.SizeValidator(32 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
            validators.MimetypeValidator(['image/jpeg', 'image/bmp', 'image/Png']),
            validators.ImageMinSizeValidator(640, 480),
            validators.ImageMaxSizeValidator(1920, 1440),
        ])
        field.contribute_to_class(Page, 'image')

        assert field.get_validation() == {
            'sizeLimit': 32 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png'),
            'minImageWidth': 640,
            'minImageHeight': 480,
            'maxImageWidth': 1920,
            'maxImageHeight': 1440,
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 32 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png'),
            'minImageWidth': 640,
            'minImageHeight': 480,
            'maxImageWidth': 1920,
            'maxImageHeight': 1440,
        }
