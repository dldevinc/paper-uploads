import os
from pathlib import Path
from django.test import TestCase
from django.core.files import File
from tests.app.models import Page
from ..models import UploadedFile

TESTS_PATH = Path(__file__).parent / 'samples'


class TestFileField(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            self.object = UploadedFile(
                file=File(fp, name='Doc.PDF'),
            )
            self.object.save()

    def tearDown(self) -> None:
        self.object.delete()

    def test_name(self):
        self.assertEqual(self.object.name, 'Doc')

    def test_display_name(self):
        self.assertEqual(self.object.display_name, 'Doc')

    def test_extension_lowercase(self):
        self.assertEqual(self.object.extension, 'pdf')

    def test_file_size(self):
        self.assertEqual(self.object.size, 9678)

    def test_file_hash(self):
        self.assertEqual(self.object.hash, 'bebc2ddd2a8b8270b359990580ff346d14c021fa')

    def test_canonical_name(self):
        self.assertEqual(self.object.canonical_name, 'Doc.pdf')

    def test_file_exist(self):
        self.assertTrue(os.path.isfile(self.object.path))

    def test_owner_model(self):
        self.assertIsNone(self.object.get_owner_model())

    def test_owner_field(self):
        self.assertIsNone(self.object.get_owner_field())

    def test_validation(self):
        self.assertEqual(self.object.get_validation(), {})


class TestSlaveFileField(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            self.object = UploadedFile(
                file=File(fp, name='Doc.PDF'),
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='file'
            )
            self.object.save()

    def tearDown(self) -> None:
        self.object.delete()

    def test_owner_model(self):
        self.assertIs(self.object.get_owner_model(), Page)

    def test_owner_field(self):
        self.assertIs(self.object.get_owner_field(), Page._meta.get_field('file'))
