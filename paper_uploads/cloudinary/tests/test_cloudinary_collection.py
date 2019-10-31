import re
import pytest
from pathlib import Path
from django.template import loader
from django.core.files import File
from django.core.exceptions import ObjectDoesNotExist
from tests.app.models import Page, PageCloudinaryGallery, PageCloudinaryFilesGallery
from ...conf import settings
from ... import validators
from ...models.fields import CollectionField
from ..models import CloudinaryFileItem, CloudinaryMediaItem, CloudinaryImageItem

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryCollection:
    def test_collection(self):
        collection = PageCloudinaryFilesGallery.objects.create()

        try:
            assert collection.item_types.keys() == {'image', 'media', 'file'}
            assert collection.item_types['image'].model is CloudinaryImageItem
            assert collection.item_types['media'].model is CloudinaryMediaItem
            assert collection.item_types['file'].model is CloudinaryFileItem
            assert collection.get_validation() == {}

            with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
                assert collection.detect_file_type(File(jpeg_file, name='Image.Jpeg')) == 'image'

            with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
                assert collection.detect_file_type(File(svg_file, name='cartman.svg')) == 'image'

            with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
                assert collection.detect_file_type(File(pdf_file, name='Sample Document.PDF')) == 'file'

            with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
                assert collection.detect_file_type(File(audio_file, name='audio.ogg')) == 'media'
        finally:
            collection.delete()

    def test_image_collection(self):
        collection = PageCloudinaryGallery.objects.create()

        try:
            assert collection.item_types.keys() == {'image'}
            assert collection.item_types['image'].model is CloudinaryImageItem
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
        collection = PageCloudinaryFilesGallery.objects.create()
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            image_item = CloudinaryImageItem()
            image_item.attach_to(collection)
            image_item.attach_file(File(pdf_file, name='Sample Document.PDF'))
            image_item.save()

        image_item.refresh_from_db()
        assert image_item.file_exists() is True

        collection.delete()

        with pytest.raises(ObjectDoesNotExist):
            image_item.refresh_from_db()

    def test_manager(self):
        file_collection_1 = PageCloudinaryFilesGallery.objects.create()
        file_collection_2 = PageCloudinaryFilesGallery.objects.create()
        image_collection_1 = PageCloudinaryGallery.objects.create()
        image_collection_2 = PageCloudinaryGallery.objects.create()
        image_collection_3 = PageCloudinaryGallery.objects.create()

        assert PageCloudinaryFilesGallery.objects.count() == 2
        assert PageCloudinaryGallery.objects.count() == 3
        assert PageCloudinaryFilesGallery._base_manager.count() == 5
        assert PageCloudinaryGallery._base_manager.count() == 5


class TestCloudinaryFileItem:
    def test_file_support(self):
        item = CloudinaryFileItem()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is True

        with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            assert item.file_supported(File(pdf_file, name='Sample Document.PDF')) is True

        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is True

    def test_file_item(self):
        collection = PageCloudinaryFilesGallery.objects.create()

        try:
            with open(TESTS_PATH / 'sheet.xlsx', 'rb') as xls_file:
                item = CloudinaryFileItem()

                with pytest.raises(AttributeError):
                    item.attach_file(File(xls_file, name='sheet.xlsx'))

                item.attach_to(collection)
                item.attach_file(File(xls_file, name='sheet.xlsx'))
                item.full_clean()
                item.save()

            assert item.PROXY_FILE_ATTRIBUTES == {'url'}
            assert item.cloudinary_resource_type == 'raw'
            assert item.cloudinary_type == 'upload'
            assert item.file.resource_type == 'raw'
            assert item.file.type == 'upload'

            assert item.collection_id == collection.pk
            assert item.name == 'sheet'
            assert item.display_name == 'sheet'
            assert item.canonical_name == 'sheet.xlsx'
            assert item.extension == 'xlsx'
            assert item.size == 8628629
            assert item.hash == 'a8c8369de899050565873ab78ee1503fbafcc859'
            assert item.item_type == 'file'

            # TODO: нет данных от CollectionItemBase
            assert item.as_dict() == {
                'id': item.pk,
                'ext': item.extension,
                'size': item.size,

                # 'collectionId': item.collection_id,
                # 'item_type': item.item_type,
                'name': item.canonical_name,
                'url': item.get_file_url(),
                'preview': loader.render_to_string('paper_uploads/collection_item/preview/file.html', {
                    'item': item,
                    'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                    'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                })
            }

            for name in item.PROXY_FILE_ATTRIBUTES:
                assert getattr(item, name) == getattr(item.file, name)

            # SlaveModelMixin methods
            assert item.get_collection_class() is PageCloudinaryFilesGallery
            assert item.get_itemtype_field() is PageCloudinaryFilesGallery.item_types['file']

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+\.xlsx', item.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.xlsx', item.get_file_name()) is not None
            assert item.get_file_size() == 8628629
            assert item.file_exists() is True
            assert item.get_file_hash() == 'a8c8369de899050565873ab78ee1503fbafcc859'
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/raw/upload/[^/]+/sheet_\w+\.xlsx', item.get_file_url()) is not None

            # FilePreviewIconItemMixin methods
            assert item.get_preview_url() == '/static/paper_uploads/dist/image/xls.svg'
        finally:
            collection.delete()


class TestCloudinaryMediaItem:
    def test_file_support(self):
        item = CloudinaryMediaItem()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is False

        with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is False

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            assert item.file_supported(File(pdf_file, name='Sample Document.PDF')) is False

        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is True

    def test_media_item(self):
        collection = PageCloudinaryFilesGallery.objects.create()

        try:
            with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
                item = CloudinaryMediaItem()

                with pytest.raises(AttributeError):
                    item.attach_file(File(audio_file, name='audio.ogg'))

                item.attach_to(collection)
                item.attach_file(File(audio_file, name='audio.ogg'))
                item.full_clean()
                item.save()

            assert item.PROXY_FILE_ATTRIBUTES == {'url'}
            assert item.cloudinary_resource_type == 'video'
            assert item.cloudinary_type == 'upload'
            assert item.file.resource_type == 'video'
            assert item.file.type == 'upload'

            assert item.collection_id == collection.pk
            assert item.name == 'audio'
            assert item.display_name == 'audio'
            assert item.canonical_name == 'audio.ogg'
            assert item.extension == 'ogg'
            assert item.size == 105243
            assert item.hash == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'
            assert item.item_type == 'media'

            # TODO: нет данных от CollectionItemBase
            assert item.as_dict() == {
                'id': item.pk,
                'ext': item.extension,
                'size': item.size,

                # 'collectionId': item.collection_id,
                # 'item_type': item.item_type,
                'name': item.canonical_name,
                'url': item.get_file_url(),
                'preview': loader.render_to_string('paper_uploads/collection_item/preview/file.html', {
                    'item': item,
                    'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                    'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                })
            }

            for name in item.PROXY_FILE_ATTRIBUTES:
                assert getattr(item, name) == getattr(item.file, name)

            # SlaveModelMixin methods
            assert item.get_collection_class() is PageCloudinaryFilesGallery
            assert item.get_itemtype_field() is PageCloudinaryFilesGallery.item_types['media']

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+', item.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.ogg', item.get_file_name()) is not None
            assert item.get_file_size() == 105243
            assert item.file_exists() is True
            assert item.get_file_hash() == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/video/upload/[^/]+/audio_\w+\.ogg', item.get_file_url()) is not None

            # FilePreviewIconItemMixin methods
            assert item.get_preview_url() == '/static/paper_uploads/dist/image/audio.svg'
        finally:
            collection.delete()


class TestCloudinaryImageItem:
    def test_file_support(self):
        item = CloudinaryImageItem()

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is True

        with open(TESTS_PATH / 'cartman.svg', 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            assert item.file_supported(File(pdf_file, name='Sample Document.PDF')) is False

        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is False

    def test_image_item(self):
        collection = PageCloudinaryFilesGallery.objects.create()

        try:
            with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
                item = CloudinaryImageItem(
                    alt='Alternate text',
                    title='Image title',
                )

                with pytest.raises(AttributeError):
                    item.attach_file(File(jpeg_file, name='Image.Jpeg'))

                item.attach_to(collection)
                item.attach_file(File(jpeg_file, name='Image.Jpeg'))
                item.full_clean()
                item.save()

            assert item.PROXY_FILE_ATTRIBUTES == {'url'}
            assert item.cloudinary_resource_type == 'image'
            assert item.cloudinary_type == 'upload'
            assert item.file.resource_type == 'image'
            assert item.file.type == 'upload'

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

            # TODO: нет данных от CollectionItemBase
            assert item.as_dict() == {
                'id': item.pk,
                'ext': item.extension,
                'size': item.size,

                # 'collectionId': item.collection_id,
                # 'item_type': item.item_type,
                'name': item.canonical_name,
                'url': item.get_file_url(),
                'preview': loader.render_to_string('paper_uploads/collection_item/preview/cloudinary_image.html', {
                    'item': item,
                    'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                    'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                })
            }

            for name in item.PROXY_FILE_ATTRIBUTES:
                assert getattr(item, name) == getattr(item.file, name)

            # SlaveModelMixin methods
            assert item.get_collection_class() is PageCloudinaryFilesGallery
            assert item.get_itemtype_field() is PageCloudinaryFilesGallery.item_types['image']

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+', item.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.jpg', item.get_file_name()) is not None
            assert item.get_file_size() == 214779
            assert item.file_exists() is True
            assert item.get_file_hash() == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/image/upload/[^/]+/Image_\w+\.jpg', item.get_file_url()) is not None
        finally:
            collection.delete()


class TestCollectionField:
    def test_rel(self):
        field = CollectionField(PageCloudinaryGallery)
        assert field.null is True
        assert field.blank is True
        assert field.related_model is PageCloudinaryGallery

    def test_validators(self):
        field = CollectionField(PageCloudinaryGallery, validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
        ])
        field.contribute_to_class(Page, 'cloud_gallery')

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
