import os
from pathlib import Path
from django.test import TestCase
from django.core.files import File
from ..models import GallerySVGItem, GalleryImageItem, GalleryFileItem
from ..conf import PROXY_FILE_ATTRIBUTES
from tests.app.models import PageGallery, PageFilesGallery

TESTS_PATH = Path(__file__).parent / 'samples'


class TestGallery(TestCase):
    def setUp(self) -> None:
        self.gallery = PageFilesGallery.objects.create()

        with open(TESTS_PATH / 'cartman.svg', 'rb') as fp:
            self.svg_item = GallerySVGItem(
                file=File(fp, name='cartman.Svg'),
            )
            self.svg_item.attach_to(self.gallery)
            self.svg_item.full_clean()
            self.svg_item.save()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.image_item = GalleryImageItem(
                file=File(fp, name='Image.Jpeg'),
                alt='Alternate text',
                title='Image title',
            )
            self.image_item.attach_to(self.gallery)
            self.image_item.full_clean()
            self.image_item.save()

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            self.file_item = GalleryFileItem(
                file=File(fp, name='Doc.PDF'),
            )
            self.file_item.attach_to(self.gallery)
            self.file_item.full_clean()
            self.file_item.save()

        with open(TESTS_PATH / 'audio.ogg', 'rb') as fp:
            self.audio_item = GalleryFileItem(
                file=File(fp, name='audio.ogg'),
            )
            self.audio_item.attach_to(self.gallery)
            self.audio_item.full_clean()
            self.audio_item.save()

    def tearDown(self) -> None:
        self.gallery.delete()

    def test_name(self):
        self.assertEqual(self.svg_item.name, 'cartman')
        self.assertEqual(self.image_item.name, 'Image')
        self.assertEqual(self.file_item.name, 'Doc')
        self.assertEqual(self.audio_item.name, 'audio')

    def test_extension_lowercase(self):
        self.assertEqual(self.svg_item.extension, 'svg')
        self.assertEqual(self.image_item.extension, 'jpeg')
        self.assertEqual(self.file_item.extension, 'pdf')
        self.assertEqual(self.audio_item.extension, 'ogg')

    def test_file_size(self):
        self.assertEqual(self.svg_item.size, 1183)
        self.assertEqual(self.image_item.size, 214779)
        self.assertEqual(self.file_item.size, 9678)
        self.assertEqual(self.audio_item.size, 105243)

    def test_file_hash(self):
        self.assertEqual(self.svg_item.hash, '0de603d9b61a3af301f23a0f233113119f5368f5')
        self.assertEqual(self.image_item.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')
        self.assertEqual(self.file_item.hash, 'bebc2ddd2a8b8270b359990580ff346d14c021fa')
        self.assertEqual(self.audio_item.hash, '4fccac8855634c2dccbd806aa7fc4ac3879e5a35')

    def test_canonical_name(self):
        self.assertEqual(self.svg_item.canonical_name, 'cartman.svg')
        self.assertEqual(self.image_item.canonical_name, 'Image.jpeg')
        self.assertEqual(self.file_item.canonical_name, 'Doc.pdf')
        self.assertEqual(self.audio_item.canonical_name, 'audio.ogg')

    def test_file_exist(self):
        self.assertTrue(os.path.isfile(self.svg_item.path))
        self.assertTrue(os.path.isfile(self.image_item.path))
        self.assertTrue(os.path.isfile(self.file_item.path))
        self.assertTrue(os.path.isfile(self.audio_item.path))

    def test_item_type(self):
        self.assertEqual(self.svg_item.item_type, 'svg')
        self.assertEqual(self.image_item.item_type, 'image')
        self.assertEqual(self.file_item.item_type, 'file')
        self.assertEqual(self.audio_item.item_type, 'file')

    def test_alt(self):
        self.assertEqual(self.image_item.alt, 'Alternate text')

    def test_title(self):
        self.assertEqual(self.image_item.title, 'Image title')

    def test_width(self):
        self.assertEqual(self.image_item.width, 1600)

    def test_height(self):
        self.assertEqual(self.image_item.height, 1200)

    def test_cropregion(self):
        self.assertEqual(self.image_item.cropregion, '')

    def test_owner_model(self):
        self.assertIsNone(self.gallery.get_owner_model())

    def test_owner_field(self):
        self.assertIsNone(self.gallery.get_owner_field())

    def test_validation(self):
        self.assertEqual(self.gallery.get_validation(), {})

    def test_get_variations(self):
        variations = self.image_item.get_variations()
        self.assertIn('admin_preview', variations)
        self.assertIn('admin_preview_2x', variations)
        self.assertIn('admin_preview_webp', variations)
        self.assertIn('admin_preview_webp_2x', variations)

    def test_get_gallery_class(self):
        self.assertIs(self.svg_item.get_gallery_class(), PageFilesGallery)
        self.assertIs(self.image_item.get_gallery_class(), PageFilesGallery)
        self.assertIs(self.file_item.get_gallery_class(), PageFilesGallery)
        self.assertIs(self.audio_item.get_gallery_class(), PageFilesGallery)

    def test_get_gallery_field(self):
        self.assertIs(self.svg_item.get_gallery_field(), PageFilesGallery.item_types['svg'])
        self.assertIs(self.image_item.get_gallery_field(), PageFilesGallery.item_types['image'])
        self.assertIs(self.file_item.get_gallery_field(), PageFilesGallery.item_types['file'])
        self.assertIs(self.audio_item.get_gallery_field(), PageFilesGallery.item_types['file'])

    def test_display_name(self):
        self.assertEqual(self.svg_item.display_name, 'cartman')
        self.assertEqual(self.file_item.display_name, 'Doc')
        self.assertEqual(self.audio_item.display_name, 'audio')

    def test_get_invalid_variation_file(self):
        with self.assertRaises(KeyError):
            self.image_item.get_variation_file('nonexist')

    def test_proxy_attrs(self):
        for name in PROXY_FILE_ATTRIBUTES:
            with self.subTest(name):
                self.assertEqual(
                    getattr(self.svg_item, name),
                    getattr(self.svg_item.file, name),
                )
                self.assertEqual(
                    getattr(self.image_item, name),
                    getattr(self.image_item.file, name),
                )
                self.assertEqual(
                    getattr(self.file_item, name),
                    getattr(self.file_item.file, name),
                )
                self.assertEqual(
                    getattr(self.audio_item, name),
                    getattr(self.audio_item.file, name),
                )

    def test_proxy_gallery(self):
        self.assertTrue(PageFilesGallery._meta.proxy)

    def test_item_types(self):
        self.assertSequenceEqual(
            list(PageFilesGallery.item_types.keys()),
            ['svg', 'image', 'file']
        )

    def test_gallery_manager(self):
        self.assertNotIn(self.gallery.pk, PageGallery.objects.values('pk'))

    def test_get_items(self):
        self.assertIs(self.gallery.get_items('svg').count(), 1)
        self.assertIs(self.gallery.get_items('image').count(), 1)
        self.assertIs(self.gallery.get_items('file').count(), 2)

    def test_get_items_total(self):
        self.assertIs(self.gallery.get_items().count(), 4)

    def test_invalid_get_items(self):
        with self.assertRaises(ValueError):
            self.gallery.get_items('something')

    def test_file_preview(self):
        self.assertEqual(self.file_item.preview, '/static/paper_uploads/dist/image/pdf.svg')
        self.assertEqual(self.audio_item.preview, '/static/paper_uploads/dist/image/unknown.svg')


class TestImageGallery(TestCase):
    def setUp(self) -> None:
        self.gallery = PageGallery.objects.create()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.image_item = GalleryImageItem(
                file=File(fp, name='Image.Jpeg'),
                alt='Alternate text',
                title='Image title',
            )
            self.image_item.attach_to(self.gallery)
            self.image_item.full_clean()
            self.image_item.save()

    def tearDown(self) -> None:
        self.gallery.delete()

    def test_name(self):
        self.assertEqual(self.image_item.name, 'Image')

    def test_extension_lowercase(self):
        self.assertEqual(self.image_item.extension, 'jpeg')

    def test_file_size(self):
        self.assertEqual(self.image_item.size, 214779)

    def test_file_hash(self):
        self.assertEqual(self.image_item.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')

    def test_canonical_name(self):
        self.assertEqual(self.image_item.canonical_name, 'Image.jpeg')

    def test_file_exist(self):
        self.assertTrue(os.path.isfile(self.image_item.path))

    def test_item_type(self):
        self.assertEqual(self.image_item.item_type, 'image')

    def test_alt(self):
        self.assertEqual(self.image_item.alt, 'Alternate text')

    def test_title(self):
        self.assertEqual(self.image_item.title, 'Image title')

    def test_width(self):
        self.assertEqual(self.image_item.width, 1600)

    def test_height(self):
        self.assertEqual(self.image_item.height, 1200)

    def test_cropregion(self):
        self.assertEqual(self.image_item.cropregion, '')

    def test_owner_model(self):
        self.assertIsNone(self.gallery.get_owner_model())

    def test_owner_field(self):
        self.assertIsNone(self.gallery.get_owner_field())

    def test_validation(self):
        self.assertIn('acceptFiles', self.gallery.get_validation())

    def test_get_variations(self):
        variations_ext = self.image_item.get_variations()
        self.assertIn('wide_raw', variations_ext)
        self.assertIn('wide', variations_ext)
        self.assertIn('desktop', variations_ext)
        self.assertIn('tablet', variations_ext)
        self.assertIn('mobile', variations_ext)
        self.assertIn('admin_preview', variations_ext)
        self.assertIn('admin_preview_2x', variations_ext)
        self.assertIn('admin_preview_webp', variations_ext)
        self.assertIn('admin_preview_webp_2x', variations_ext)

    def test_get_gallery_class(self):
        self.assertIs(self.image_item.get_gallery_class(), PageGallery)

    def test_get_gallery_field(self):
        self.assertIs(self.image_item.get_gallery_field(), PageGallery.item_types['image'])

    def test_get_invalid_variation_file(self):
        with self.assertRaises(KeyError):
            self.image_item.get_variation_file('nonexist')

    def test_proxy_attrs(self):
        for name in PROXY_FILE_ATTRIBUTES:
            with self.subTest(name):
                self.assertEqual(
                    getattr(self.image_item, name),
                    getattr(self.image_item.file, name),
                )

    def test_proxy_gallery(self):
        self.assertTrue(PageGallery._meta.proxy)

    def test_item_types(self):
        self.assertSequenceEqual(
            list(PageGallery.item_types.keys()),
            ['image']
        )

    def test_gallery_manager(self):
        self.assertNotIn(self.gallery.pk, PageFilesGallery.objects.values('pk'))

    def test_get_items(self):
        self.assertIs(self.gallery.get_items('image').count(), 1)

    def test_get_items_total(self):
        self.assertIs(self.gallery.get_items().count(), 1)

    def test_invalid_get_items(self):
        with self.assertRaises(ValueError):
            self.gallery.get_items('something')
