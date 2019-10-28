from pathlib import Path
from django.test import TestCase
from django.core.files import File
from ...models.fields import CollectionField
from ...cloudinary.models import CloudinaryFileItem, CloudinaryImageItem, CloudinaryMediaItem
from ... import validators
from tests.app.models import Page, PageCloudinaryGallery, PageCloudinaryFilesGallery

TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestImageItemException(TestCase):
    def test_exception(self):
        self.collection = PageCloudinaryFilesGallery.objects.create()

        with self.assertRaises(RuntimeError):
            with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
                self.image_item = CloudinaryImageItem()
                self.image_item.attach_file(File(fp, name='Image.Jpeg'))
                self.image_item.attach_to(self.collection)
                self.image_item.save()


class TestCollection(TestCase):
    def setUp(self) -> None:
        self.collection = PageCloudinaryFilesGallery.objects.create()

        with open(TESTS_PATH / 'cartman.svg', 'rb') as fp:
            self.svg_image_item = CloudinaryImageItem()
            self.svg_image_item.attach_to(self.collection)
            self.svg_image_item.attach_file(File(fp, name='cartman.Svg'))
            self.svg_image_item.full_clean()
            self.svg_image_item.save()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.image_item = CloudinaryImageItem(
                alt='Alternate text',
                title='Image title',
            )
            self.image_item.attach_to(self.collection)
            self.image_item.attach_file(File(fp, name='Image.Jpeg'))
            self.image_item.full_clean()
            self.image_item.save()

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            self.file_item = CloudinaryFileItem()
            self.file_item.attach_to(self.collection)
            self.file_item.attach_file(File(fp, name='Doc.PDF'))
            self.file_item.full_clean()
            self.file_item.save()

        with open(TESTS_PATH / 'audio.ogg', 'rb') as fp:
            self.audio_item = CloudinaryMediaItem()
            self.audio_item.attach_to(self.collection)
            self.audio_item.attach_file(File(fp, name='audio.ogg'))
            self.audio_item.full_clean()
            self.audio_item.save()

    def tearDown(self) -> None:
        self.collection.delete()

    def test_name(self):
        self.assertEqual(self.svg_image_item.name, 'cartman')
        self.assertEqual(self.image_item.name, 'Image')
        self.assertEqual(self.file_item.name, 'Doc')
        self.assertEqual(self.audio_item.name, 'audio')

    def test_extension_lowercase(self):
        self.assertEqual(self.svg_image_item.extension, 'svg')
        self.assertEqual(self.image_item.extension, 'jpg')
        self.assertEqual(self.file_item.extension, 'pdf')
        self.assertEqual(self.audio_item.extension, 'ogg')

    def test_file_size(self):
        self.assertEqual(self.svg_image_item.size, 1183)
        self.assertEqual(self.image_item.size, 214779)
        self.assertEqual(self.file_item.size, 9678)
        self.assertEqual(self.audio_item.size, 105243)

    def test_file_hash(self):
        self.assertEqual(self.svg_image_item.hash, '0de603d9b61a3af301f23a0f233113119f5368f5')
        self.assertEqual(self.image_item.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')
        self.assertEqual(self.file_item.hash, 'bebc2ddd2a8b8270b359990580ff346d14c021fa')
        self.assertEqual(self.audio_item.hash, '4fccac8855634c2dccbd806aa7fc4ac3879e5a35')

    def test_canonical_name(self):
        self.assertEqual(self.svg_image_item.canonical_name, 'cartman.svg')
        self.assertEqual(self.image_item.canonical_name, 'Image.jpg')
        self.assertEqual(self.file_item.canonical_name, 'Doc.pdf')
        self.assertEqual(self.audio_item.canonical_name, 'audio.ogg')

    def test_item_type(self):
        self.assertEqual(self.svg_image_item.item_type, 'image')
        self.assertEqual(self.image_item.item_type, 'image')
        self.assertEqual(self.file_item.item_type, 'file')
        self.assertEqual(self.audio_item.item_type, 'media')

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
        self.assertIsNone(self.collection.get_owner_model())

    def test_owner_field(self):
        self.assertIsNone(self.collection.get_owner_field())

    def test_validation(self):
        self.assertEqual(self.collection.get_validation(), {})

    def test_get_collection_class(self):
        self.assertIs(self.svg_image_item.get_collection_class(), PageCloudinaryFilesGallery)
        self.assertIs(self.image_item.get_collection_class(), PageCloudinaryFilesGallery)
        self.assertIs(self.file_item.get_collection_class(), PageCloudinaryFilesGallery)
        self.assertIs(self.audio_item.get_collection_class(), PageCloudinaryFilesGallery)

    def test_get_itemtype_field(self):
        self.assertIs(self.svg_image_item.get_itemtype_field(), PageCloudinaryFilesGallery.item_types['image'])
        self.assertIs(self.image_item.get_itemtype_field(), PageCloudinaryFilesGallery.item_types['image'])
        self.assertIs(self.file_item.get_itemtype_field(), PageCloudinaryFilesGallery.item_types['file'])
        self.assertIs(self.audio_item.get_itemtype_field(), PageCloudinaryFilesGallery.item_types['media'])

    def test_display_name(self):
        self.assertEqual(self.file_item.display_name, 'Doc')
        self.assertEqual(self.audio_item.display_name, 'audio')

    def test_proxy_attrs(self):
        items = (
            ('svg', self.svg_image_item),
            ('image', self.image_item),
            ('file', self.file_item),
            ('audio', self.audio_item),
        )
        for code, item in items:
            for name in item.PROXY_FILE_ATTRIBUTES:
                with self.subTest('{}.{}'.format(code, name)):
                    self.assertEqual(
                        getattr(item, name),
                        getattr(item.file, name),
                    )

    def test_proxy_collection(self):
        self.assertTrue(PageCloudinaryFilesGallery._meta.proxy)

    def test_item_types(self):
        self.assertSequenceEqual(
            list(PageCloudinaryFilesGallery.item_types.keys()),
            ['image', 'media', 'file']
        )

    def test_collection_manager(self):
        self.assertNotIn(self.collection.pk, PageCloudinaryGallery.objects.values('pk'))

    def test_get_items(self):
        self.assertIs(self.collection.get_items('image').count(), 2)
        self.assertIs(self.collection.get_items('media').count(), 1)
        self.assertIs(self.collection.get_items('file').count(), 1)

    def test_get_items_total(self):
        self.assertIs(self.collection.get_items().count(), 4)

    def test_item_collection_id(self):
        for item in self.collection.items.all():
            self.assertEqual(item.collection_id, self.collection.pk)
            self.assertEqual(item.collection, self.collection)

    def test_invalid_get_items(self):
        with self.assertRaises(ValueError):
            self.collection.get_items('something')

    def test_file_preview(self):
        self.assertEqual(self.file_item.preview, '/static/paper_uploads/dist/image/pdf.svg')
        self.assertEqual(self.audio_item.preview, '/static/paper_uploads/dist/image/audio.svg')

    def test_svg_item_as_dict(self):
        self.assertDictContainsSubset(
            {
                'id': 1,
                'collectionId': 1,
                'item_type': 'image',
                'name': 'cartman.svg',
            },
            self.svg_image_item.as_dict(),
        )

    def test_image_item_as_dict(self):
        self.assertDictContainsSubset(
            {
                'id': 2,
                'collectionId': 1,
                'item_type': 'image',
                'name': 'Image.jpg',
            },
            self.image_item.as_dict(),
        )

    def test_file_item_as_dict(self):
        self.assertDictContainsSubset(
            {
                'id': 3,
                'collectionId': 1,
                'item_type': 'file',
                'name': 'Doc.pdf',
            },
            self.file_item.as_dict(),
        )

    def test_audio_item_as_dict(self):
        self.assertDictContainsSubset(
            {
                'id': 4,
                'collectionId': 1,
                'item_type': 'media',
                'name': 'audio.ogg',
            },
            self.audio_item.as_dict(),
        )


class TestImageCollection(TestCase):
    def setUp(self) -> None:
        self.collection = PageCloudinaryGallery.objects.create()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.image_item = CloudinaryImageItem(
                alt='Alternate text',
                title='Image title',
            )
            self.image_item.attach_to(self.collection)
            self.image_item.attach_file(File(fp, name='Image.Jpeg'))
            self.image_item.full_clean()
            self.image_item.save()

    def tearDown(self) -> None:
        self.collection.delete()

    def test_name(self):
        self.assertEqual(self.image_item.name, 'Image')

    def test_extension_lowercase(self):
        self.assertEqual(self.image_item.extension, 'jpg')

    def test_file_size(self):
        self.assertEqual(self.image_item.size, 214779)

    def test_file_hash(self):
        self.assertEqual(self.image_item.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')

    def test_canonical_name(self):
        self.assertEqual(self.image_item.canonical_name, 'Image.jpg')

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
        self.assertIsNone(self.collection.get_owner_model())

    def test_owner_field(self):
        self.assertIsNone(self.collection.get_owner_field())

    def test_validation(self):
        self.assertIn('acceptFiles', self.collection.get_validation())

    def test_get_collection_class(self):
        self.assertIs(self.image_item.get_collection_class(), PageCloudinaryGallery)

    def test_get_itemtype_field(self):
        self.assertIs(self.image_item.get_itemtype_field(), PageCloudinaryGallery.item_types['image'])

    def test_proxy_attrs(self):
        for name in self.image_item.PROXY_FILE_ATTRIBUTES:
            with self.subTest(name):
                self.assertEqual(
                    getattr(self.image_item, name),
                    getattr(self.image_item.file, name),
                )

    def test_proxy_collection(self):
        self.assertTrue(PageCloudinaryGallery._meta.proxy)

    def test_item_types(self):
        self.assertSequenceEqual(
            list(PageCloudinaryGallery.item_types.keys()),
            ['image']
        )

    def test_collection_manager(self):
        self.assertNotIn(self.collection.pk, PageCloudinaryFilesGallery.objects.values('pk'))

    def test_get_items(self):
        self.assertIs(self.collection.get_items('image').count(), 1)

    def test_get_items_total(self):
        self.assertIs(self.collection.get_items().count(), 1)

    def test_item_collection_id(self):
        for item in self.collection.items.all():
            self.assertEqual(item.collection_id, self.collection.pk)
            self.assertEqual(item.collection, self.collection)

    def test_invalid_get_items(self):
        with self.assertRaises(ValueError):
            self.collection.get_items('something')


class TestCollectionField(TestCase):
    def setUp(self) -> None:
        self.field = CollectionField(PageCloudinaryGallery, validators=[
            validators.SizeValidator(32 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
        ])
        self.field.contribute_to_class(Page, 'cloud_gallery')

    def test_validation(self):
        self.assertDictEqual(self.field.get_validation(), {
            'sizeLimit': 32 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
        })

    def test_widget_validation(self):
        formfield = self.field.formfield()
        self.assertDictEqual(formfield.widget.get_validation(), {
            'sizeLimit': 32 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': 'image/*'
        })
