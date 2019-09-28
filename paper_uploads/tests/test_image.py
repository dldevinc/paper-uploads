import os
from pathlib import Path
from django.test import TestCase
from django.core.files import File
from tests.app.models import Page
from ..models import UploadedImage
from ..models.fields import ImageField
from ..conf import PROXY_FILE_ATTRIBUTES
from .. import validators

TESTS_PATH = Path(__file__).parent / 'samples'


class TestUploadedImage(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.object = UploadedImage(
                file=File(fp, name='Image.Jpeg'),
                alt='Alternate text',
                title='Image title',
            )
            self.object.save()

    def tearDown(self) -> None:
        self.object.delete()

    def test_name(self):
        self.assertEqual(self.object.name, 'Image')

    def test_extension_lowercase(self):
        self.assertEqual(self.object.extension, 'jpeg')

    def test_file_size(self):
        self.assertEqual(self.object.size, 214779)

    def test_file_hash(self):
        self.assertEqual(self.object.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')

    def test_canonical_name(self):
        self.assertEqual(self.object.canonical_name, 'Image.jpeg')

    def test_file_exist(self):
        self.assertTrue(os.path.isfile(self.object.path))

    def test_alt(self):
        self.assertEqual(self.object.alt, 'Alternate text')

    def test_title(self):
        self.assertEqual(self.object.title, 'Image title')

    def test_width(self):
        self.assertEqual(self.object.width, 1600)

    def test_height(self):
        self.assertEqual(self.object.height, 1200)

    def test_cropregion(self):
        self.assertEqual(self.object.cropregion, '')

    def test_owner_model(self):
        self.assertIsNone(self.object.get_owner_model())

    def test_owner_field(self):
        self.assertIsNone(self.object.get_owner_field())

    def test_validation(self):
        self.assertIn('acceptFiles', self.object.get_validation())

    def test_proxy_attrs(self):
        for name in PROXY_FILE_ATTRIBUTES:
            with self.subTest(name):
                self.assertEqual(
                    getattr(self.object, name),
                    getattr(self.object.file, name),
                )


class TestSlaveUploadedImage(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.object = UploadedImage(
                file=File(fp, name='TestImage.Jpeg'),
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='image_ext'
            )
            self.object.save()

    def tearDown(self) -> None:
        self.object.delete()

    def test_owner_model(self):
        self.assertIs(self.object.get_owner_model(), Page)

    def test_owner_field(self):
        self.assertIs(self.object.get_owner_field(), Page._meta.get_field('image_ext'))

    def test_get_variations(self):
        variations = self.object.get_variations()
        self.assertIn('desktop', variations)
        self.assertIn('tablet', variations)
        self.assertIn('admin', variations)

    def test_variation_attrs(self):
        variations = dict(self.object.get_variation_files())
        self.assertEqual(getattr(self.object, 'desktop'), variations['desktop'])
        self.assertEqual(getattr(self.object, 'tablet'), variations['tablet'])
        self.assertEqual(getattr(self.object, 'admin'), variations['admin'])

    def test_get_invalid_variation_file(self):
        with self.assertRaises(KeyError):
            self.object.get_variation_file('nonexist')

    def test_get_variation_files(self):
        expected = {
            'admin': 'TestImage.admin.jpg',
            'desktop': 'TestImage.desktop.jpg',
            'tablet': 'TestImage.tablet.jpg',
        }
        self.assertDictEqual({
            name: os.path.basename(file.name)
            for name, file in self.object.get_variation_files()
        }, expected)

    def test_get_draft_size(self):
        expected = {
            (3000, 2000): (1600, 1067),
            (1400, 1200): (1600, 1200),
            (800, 600): (1600, 600),
        }
        for input_size, output_size in expected.items():
            with self.subTest(input_size):
                self.assertSequenceEqual(
                    self.object.get_draft_size(input_size),
                    output_size
                )


class TestImageField(TestCase):
    def setUp(self) -> None:
        self.field = ImageField(validators=[
            validators.SizeValidator(32 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
            validators.MimetypeValidator(['image/jpeg', 'image/bmp', 'image/Png']),
            validators.ImageMinSizeValidator(640, 480),
            validators.ImageMaxSizeValidator(1920, 1440),
        ])
        self.field.contribute_to_class(Page, 'image')

    def test_validation(self):
        self.assertDictEqual(self.field.get_validation(), {
            'sizeLimit': 32 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png'),
            'minImageWidth': 640,
            'minImageHeight': 480,
            'maxImageWidth': 1920,
            'maxImageHeight': 1440,
        })

    def test_widget_validation(self):
        formfield = self.field.formfield()
        self.assertDictEqual(formfield.widget.get_validation(), {
            'sizeLimit': 32 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png'),
            'minImageWidth': 640,
            'minImageHeight': 480,
            'maxImageWidth': 1920,
            'maxImageHeight': 1440,
        })
