from pathlib import Path
from django.test import TestCase
from django.core.files import File
from tests.app.models import Page
from ..models import CloudinaryImage

TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryImage(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.object = CloudinaryImage(
                alt='Alternate text',
                title='Image title',
            )
            self.object.attach_file(File(fp, name='Image.Jpeg'))
            self.object.save()

    def tearDown(self) -> None:
        self.object.delete()

    def test_name(self):
        self.assertEqual(self.object.name, 'Image')

    def test_extension_lowercase(self):
        # Cloudinary replaces extension
        self.assertEqual(self.object.extension, 'jpg')

    def test_file_size(self):
        self.assertEqual(self.object.size, 214779)

    def test_file_hash(self):
        self.assertEqual(self.object.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')

    def test_canonical_name(self):
        # Cloudinary replaces extension
        self.assertEqual(self.object.canonical_name, 'Image.jpg')

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
        for name in self.object.PROXY_FILE_ATTRIBUTES:
            with self.subTest(name):
                self.assertEqual(
                    getattr(self.object, name),
                    getattr(self.object.file, name),
                )


class TestSlaveCloudinaryImage(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.object = CloudinaryImage(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_image'
            )
            self.object.attach_file(File(fp, name='TestImage.Jpeg'))
            self.object.save()

    def tearDown(self) -> None:
        self.object.delete()

    def test_owner_model(self):
        self.assertIs(self.object.get_owner_model(), Page)

    def test_owner_field(self):
        self.assertIs(self.object.get_owner_field(), Page._meta.get_field('cloud_image'))
