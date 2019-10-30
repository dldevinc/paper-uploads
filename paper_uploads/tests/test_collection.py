import os
import re
import pytest
from pathlib import Path
from django.test import TestCase
from django.core.files import File
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from ..models import SVGItem, ImageItem, FileItem
from ..models.fields import CollectionField
from .. import validators
from tests.app.models import Page, PageGallery, PageFilesGallery

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestCollection:
    def test_collection(self):
        collection = PageFilesGallery.objects.create()

        try:
            assert collection.item_types.keys() == {'image', 'svg', 'file'}
            assert collection.item_types['image'].model is ImageItem
            assert collection.item_types['svg'].model is SVGItem
            assert collection.item_types['file'].model is FileItem
            assert collection.get_validation() == {}

            with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
                assert collection.detect_file_type(File(jpeg_file, name='Image.Jpeg')) == 'image'

            with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
                assert collection.detect_file_type(File(svg_file, name='cartman.svg')) == 'svg'

            with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
                assert collection.detect_file_type(File(pdf_file, name='Sample Document.PDF')) == 'file'

            with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
                assert collection.detect_file_type(File(audio_file, name='audio.ogg')) == 'file'
        finally:
            collection.delete()

    def test_image_collection(self):
        collection = PageGallery.objects.create()

        try:
            assert collection.item_types.keys() == {'image'}
            assert collection.item_types['image'].model is ImageItem
            assert collection.get_validation() == {
                'acceptFiles': ['image/*']
            }

            with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
                assert collection.detect_file_type(File(jpeg_file, name='Image.Jpeg')) == 'image'

            with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
                assert collection.detect_file_type(File(svg_file, name='cartman.svg')) == 'image'

            with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
                assert collection.detect_file_type(File(pdf_file, name='Sample Document.PDF')) == 'image'

            with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
                assert collection.detect_file_type(File(audio_file, name='audio.ogg')) == 'image'
        finally:
            collection.delete()

    def test_collection_cleanup(self):
        collection = PageFilesGallery.objects.create()
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            image_item = ImageItem()
            image_item.attach_to(collection)
            image_item.attach_file(File(jpeg_file, name='Image.Jpeg'))
            image_item.save()

        image_item.refresh_from_db()
        assert image_item.file_exists() is True

        collection.delete()

        with pytest.raises(ObjectDoesNotExist):
            image_item.refresh_from_db()

    def test_manager(self):
        file_collection_1 = PageFilesGallery.objects.create()
        file_collection_2 = PageFilesGallery.objects.create()
        image_collection_1 = PageGallery.objects.create()
        image_collection_2 = PageGallery.objects.create()
        image_collection_3 = PageGallery.objects.create()

        assert PageFilesGallery.objects.count() == 2
        assert PageGallery.objects.count() == 3
        assert PageFilesGallery._base_manager.count() == 5
        assert PageGallery._base_manager.count() == 5


class TestFileItem:
    def test_file_support(self):
        item = FileItem()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is True

        with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            assert item.file_supported(File(pdf_file, name='Sample Document.PDF')) is True

        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is True

    def test_file_item(self):
        collection = PageFilesGallery.objects.create()

        try:
            with open(TESTS_PATH / 'sheet.xlsx', 'rb') as xls_file:
                item = FileItem()
                # item.attach_file(File(xls_file, name='sheet.xlsx'))
                item.attach_to(collection)
                item.attach_file(File(xls_file, name='sheet.xlsx'))
                item.full_clean()
                item.save()

            suffix = re.match(r'sheet((?:_\w+)?)', os.path.basename(item.file.name)).group(1)

            assert item.PROXY_FILE_ATTRIBUTES == {'url', 'path', 'open', 'read', 'close', 'closed'}
            assert item.collection_id == collection.pk
            assert item.name == 'sheet'
            assert item.display_name == 'sheet'
            assert item.canonical_name == 'sheet.xlsx'
            assert item.extension == 'xlsx'
            assert item.size == 8628629
            assert item.hash == 'a8c8369de899050565873ab78ee1503fbafcc859'
            assert item.item_type == 'file'

            assert os.path.isfile(item.path)

            for name in item.PROXY_FILE_ATTRIBUTES:
                assert getattr(item, name) == getattr(item.file, name)

            # SlaveModelMixin methods
            assert item.get_collection_class() is PageFilesGallery
            assert item.get_itemtype_field() is PageFilesGallery.item_types['file']

            # FileFieldContainerMixin methods
            assert item.get_file_name() == 'collections/files/{}/sheet{}.xlsx'.format(now().strftime('%Y-%m-%d'), suffix)
            assert item.get_file_size() == 8628629
            assert item.file_exists() is True
            assert item.get_file_hash() == 'a8c8369de899050565873ab78ee1503fbafcc859'
            assert item.get_file_url() == '/media/collections/files/{}/sheet{}.xlsx'.format(now().strftime('%Y-%m-%d'), suffix)

            # FilePreviewIconItemMixin methods
            assert item.get_preview_url() == '/static/paper_uploads/dist/image/xls.svg'
        finally:
            collection.delete()


class TestImageItem:
    def test_file_support(self):
        item = ImageItem()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is True

        with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            assert item.file_supported(File(pdf_file, name='Sample Document.PDF')) is False

        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is False

    def test_image_item(self):
        collection = PageFilesGallery.objects.create()

        try:
            with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
                item = ImageItem(
                    alt='Alternate text',
                    title='Image title',
                )

                # TODO: вызывает рекурсию
                # with pytest.raises(AttributeError):
                #     item.attach_file(File(jpeg_file, name='Image.Jpeg'))

                item.attach_to(collection)
                item.attach_file(File(jpeg_file, name='Image.Jpeg'))
                item.full_clean()
                item.save()

            suffix = re.match(r'Image((?:_\w+)?)', os.path.basename(item.file.name)).group(1)

            assert item.PROXY_FILE_ATTRIBUTES == {'url', 'path', 'open', 'read', 'close', 'closed'}
            assert item.collection_id == collection.pk
            assert item.name == 'Image'
            assert item.canonical_name == 'Image.jpg'
            assert item.extension == 'jpg'
            assert item.size == 214779
            assert item.hash == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert item.alt == 'Alternate text'
            assert item.title == 'Image title'
            assert item.width == 1600
            assert item.height == 1200
            assert item.cropregion == ''
            assert item.item_type == 'image'

            for name in item.PROXY_FILE_ATTRIBUTES:
                assert getattr(item, name) == getattr(item.file, name)

            # SlaveModelMixin methods
            assert item.get_collection_class() is PageFilesGallery
            assert item.get_itemtype_field() is PageFilesGallery.item_types['image']

            # FileFieldContainerMixin methods
            assert item.get_file_name() == 'collections/images/{}/Image{}.jpg'.format(now().strftime('%Y-%m-%d'), suffix)
            assert item.get_file_size() == 214779
            assert item.file_exists() is True
            assert item.get_file_hash() == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert item.get_file_url() == '/media/collections/images/{}/Image{}.jpg'.format(now().strftime('%Y-%m-%d'), suffix)

            # variations
            variations = item.get_variations()
            assert 'mobile' in variations
            assert 'admin_preview' in variations
            assert 'admin_preview_2x' in variations
            assert 'admin_preview_webp' in variations
            assert 'admin_preview_webp_2x' in variations

            variation_files = dict(item.get_variation_files())
            assert getattr(item, 'mobile') is variation_files['mobile']

            with pytest.raises(KeyError):
                item.get_variation_file('nonexist')

            assert {
                name: os.path.basename(file.name)
                for name, file in item.get_variation_files()
            } == {
                'mobile': 'Image{}.mobile.jpg'.format(suffix),
                'admin_preview': 'Image{}.admin_preview.jpg'.format(suffix),
                'admin_preview_2x': 'Image{}.admin_preview_2x.jpg'.format(suffix),
                'admin_preview_webp': 'Image{}.admin_preview_webp.webp'.format(suffix),
                'admin_preview_webp_2x': 'Image{}.admin_preview_webp_2x.webp'.format(suffix),
            }

            # get_draft_size()
            expected = {
                (3000, 2000): (640, 427),
                (1400, 1200): (640, 549),
                (800, 600): (640, 480),
            }
            for input_size, output_size in expected.items():
                assert item.get_draft_size(input_size) == output_size
        finally:
            collection.delete()


class TestSVGItem:
    def test_file_support(self):
        item = SVGItem()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is False

        with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            assert item.file_supported(File(pdf_file, name='Sample Document.PDF')) is False

        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is False

    def test_svg_item(self):
        collection = PageFilesGallery.objects.create()

        try:
            with open(TESTS_PATH / 'cartman.svg', 'rb') as xls_file:
                item = SVGItem()
                # item.attach_file(File(xls_file, name='cartman.svg'))
                item.attach_to(collection)
                item.attach_file(File(xls_file, name='cartman.svg'))
                item.full_clean()
                item.save()

            suffix = re.match(r'cartman((?:_\w+)?)', os.path.basename(item.file.name)).group(1)

            assert item.PROXY_FILE_ATTRIBUTES == {'url', 'path', 'open', 'read', 'close', 'closed'}
            assert item.collection_id == collection.pk
            assert item.name == 'cartman'
            assert item.display_name == 'cartman'
            assert item.canonical_name == 'cartman.svg'
            assert item.extension == 'svg'
            assert item.size == 1022
            assert item.hash == 'f98668ff3534d61cfcef507478abfe7b4c1dbb8a'
            assert item.item_type == 'svg'

            assert os.path.isfile(item.path)

            for name in item.PROXY_FILE_ATTRIBUTES:
                assert getattr(item, name) == getattr(item.file, name)

            # SlaveModelMixin methods
            assert item.get_collection_class() is PageFilesGallery
            assert item.get_itemtype_field() is PageFilesGallery.item_types['svg']

            # FileFieldContainerMixin methods
            assert item.get_file_name() == 'collections/files/{}/cartman{}.svg'.format(now().strftime('%Y-%m-%d'), suffix)
            assert item.get_file_size() == 1022
            assert item.file_exists() is True
            assert item.get_file_hash() == 'f98668ff3534d61cfcef507478abfe7b4c1dbb8a'
            assert item.get_file_url() == '/media/collections/files/{}/cartman{}.svg'.format(now().strftime('%Y-%m-%d'), suffix)
        finally:
            collection.delete()


class TestCollectionField:
    def test_rel(self):
        field = CollectionField(PageGallery)
        assert field.null is True
        assert field.blank is True
        assert field.related_model is PageGallery

    def test_validators(self):
        field = CollectionField(PageGallery, validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
        ])
        field.contribute_to_class(Page, 'gallery')

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



#     def test_collection_manager(self):
#         self.assertNotIn(self.collection.pk, PageFilesGallery.objects.values('pk'))
#
#     def test_get_items(self):
#         self.assertIs(self.collection.get_items('image').count(), 1)
#
#     def test_get_items_total(self):
#         self.assertIs(self.collection.get_items().count(), 1)
#
#     def test_item_collection_id(self):
#         for item in self.collection.items.all():
#             self.assertEqual(item.collection_id, self.collection.pk)
#             self.assertEqual(item.collection, self.collection)
#
#     def test_invalid_get_items(self):
#         with self.assertRaises(ValueError):
#             self.collection.get_items('something')
#
#
# class TestCollectionField(TestCase):
#     def setUp(self) -> None:
#         self.field = CollectionField(PageGallery, validators=[
#             validators.SizeValidator(32 * 1024 * 1024),
#             validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
#         ])
#         self.field.contribute_to_class(Page, 'gallery')
#
#     def test_validation(self):
#         self.assertDictEqual(self.field.get_validation(), {
#             'sizeLimit': 32 * 1024 * 1024,
#             'allowedExtensions': ('svg', 'bmp', 'jpeg'),
#         })
#
#     def test_widget_validation(self):
#         formfield = self.field.formfield()
#         self.assertDictEqual(formfield.widget.get_validation(), {
#             'sizeLimit': 32 * 1024 * 1024,
#             'allowedExtensions': ('svg', 'bmp', 'jpeg'),
#             'acceptFiles': ['image/*']
#         })
