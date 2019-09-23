import os
from pathlib import Path
from django.test import TestCase
from django.core.files import File
from tests.app.models import Page
from ..models import UploadedImage
from ..conf import PROXY_FILE_ATTRIBUTES

TESTS_PATH = Path(__file__).parent / 'samples'


class TestImageField(TestCase):
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


class TestSlaveImageField(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.object = UploadedImage(
                file=File(fp, name='Image.Jpeg'),
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

    def test_get_invalid_variation_file(self):
        with self.assertRaises(KeyError):
            self.object.get_variation_file('nonexist')

    def test_get_variation_files(self):
        expected = {
            'admin': 'Image.admin.jpg',
            'desktop': 'Image.desktop.jpg',
            'tablet': 'Image.tablet.jpg',
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
