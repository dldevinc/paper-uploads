import re
from datetime import timedelta
from pathlib import Path

import pytest
from django.core.files import File
from django.template import loader
from django.utils.timezone import now
from tests.app.models import Page, PageCloudinaryFilesGallery, PageCloudinaryGallery

from ... import validators
from ...conf import settings
from ...models.fields import CollectionField
from ..models import CloudinaryFileItem, CloudinaryImageItem, CloudinaryMediaItem

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryCollection:
    def test_collection(self):
        collection = PageCloudinaryFilesGallery.objects.create(
            owner_app_label='app',
            owner_model_name='page',
            owner_fieldname='cloud_files',
        )

        try:
            assert collection.item_types.keys() == {'image', 'media', 'file'}
            assert collection.item_types['image'].model is CloudinaryImageItem
            assert collection.item_types['media'].model is CloudinaryMediaItem
            assert collection.item_types['file'].model is CloudinaryFileItem

            with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
                assert (
                    collection.detect_file_type(File(jpeg_file, name='Image.Jpeg'))
                    == 'image'
                )

            with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
                assert (
                    collection.detect_file_type(File(svg_file, name='cartman.svg'))
                    == 'image'
                )

            with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
                assert (
                    collection.detect_file_type(
                        File(pdf_file, name='Sample Document.PDF')
                    )
                    == 'file'
                )

            with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
                assert (
                    collection.detect_file_type(File(audio_file, name='audio.ogg'))
                    == 'media'
                )

            # ReverseFieldModelMixin
            assert collection.owner_app_label == 'app'
            assert collection.owner_model_name == 'page'
            assert collection.owner_fieldname == 'cloud_files'
            assert collection.get_owner_model() is Page
            assert collection.get_owner_field() is Page._meta.get_field('cloud_files')
        finally:
            collection.delete()

    def test_image_collection(self):
        collection = PageCloudinaryGallery.objects.create(
            owner_app_label='app',
            owner_model_name='page',
            owner_fieldname='cloud_gallery',
        )

        try:
            assert collection.item_types.keys() == {'image'}
            assert collection.item_types['image'].model is CloudinaryImageItem
            assert collection.get_validation() == {
                'acceptFiles': ['image/*']
            }

            with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
                assert (
                    collection.detect_file_type(File(jpeg_file, name='Image.Jpeg'))
                    == 'image'
                )

            with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
                assert (
                    collection.detect_file_type(File(svg_file, name='cartman.svg'))
                    == 'image'
                )

            with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
                assert (
                    collection.detect_file_type(
                        File(pdf_file, name='Sample Document.PDF')
                    )
                    == 'image'
                )

            with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
                assert (
                    collection.detect_file_type(File(audio_file, name='audio.ogg'))
                    == 'image'
                )

            # ReverseFieldModelMixin
            assert collection.owner_app_label == 'app'
            assert collection.owner_model_name == 'page'
            assert collection.owner_fieldname == 'cloud_gallery'
            assert collection.get_owner_model() is Page
            assert collection.get_owner_field() is Page._meta.get_field('cloud_gallery')
        finally:
            collection.delete()

    def test_manager(self):
        PageCloudinaryFilesGallery.objects.create()
        PageCloudinaryFilesGallery.objects.create()
        PageCloudinaryGallery.objects.create()
        PageCloudinaryGallery.objects.create()
        PageCloudinaryGallery.objects.create()

        assert PageCloudinaryFilesGallery.objects.count() == 2
        assert PageCloudinaryGallery.objects.count() == 3
        assert PageCloudinaryFilesGallery._base_manager.count() == 5
        assert PageCloudinaryGallery._base_manager.count() == 5


class TestCloudinaryFileItem:
    def test_file_support(self):
        item = CloudinaryFileItem()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is True

        with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            assert (
                item.file_supported(File(pdf_file, name='Sample Document.PDF')) is True
            )

        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is True

    def test_file_item(self):
        collection = PageCloudinaryFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'sheet.xlsx'), 'rb') as xls_file:
            item = CloudinaryFileItem()
            # item.attach_file(xls_file)      # <- works
            item.attach_to(collection)
            item.attach_file(xls_file)  # <- works too
            item.full_clean()
            item.save()

        try:
            # Resource
            assert item.name == 'sheet'
            assert now() - item.created_at < timedelta(seconds=10)
            assert now() - item.uploaded_at < timedelta(seconds=10)
            assert now() - item.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert item.hash == 'a8c8369de899050565873ab78ee1503fbafcc859'

            # FileResource
            assert item.extension == 'xlsx'
            assert item.size == 8628629
            assert str(item) == 'sheet.xlsx'
            assert repr(item) == "CloudinaryFileItem('sheet.xlsx')"
            assert item.get_basename() == 'sheet.xlsx'
            assert item.get_file() is item.file
            assert re.fullmatch(r'sheet_\w+\.xlsx', item.get_file_name()) is not None
            assert (
                re.fullmatch(
                    r'http://res\.cloudinary\.com/[^/]+/raw/upload/[^/]+/sheet_\w+\.xlsx',
                    item.get_file_url(),
                )
                is not None
            )
            assert item.is_file_exists() is True

            # ReadonlyFileProxyMixin
            assert item.url == item.get_file_url()

            with pytest.raises(AttributeError):
                print(item.path)

            assert item.closed is True
            with item.open():
                assert item.closed is False
                assert item.read(4) == b'PK\x03\x04'
                assert item.tell() == 4
                item.seek(0)
                assert item.tell() == 0
                assert item.closed is False
            assert item.closed is True

            # CloudinaryFileResource
            assert item.cloudinary_resource_type == 'raw'
            assert item.cloudinary_type == 'upload'

            cloudinary_field = item._meta.get_field('file')
            assert cloudinary_field.type == item.cloudinary_type
            assert cloudinary_field.resource_type == item.cloudinary_resource_type

            item.refresh_from_db()
            assert re.fullmatch(r'sheet_\w+\.xlsx', item.get_public_id()) is not None

            # CollectionResourceItem
            assert (
                item.change_form_class
                == 'paper_uploads.forms.dialogs.collection.FileItemDialog'
            )
            assert item.admin_template_name == 'paper_uploads/collection_item/file.html'
            assert item.collection_id == collection.pk
            assert (
                item.collection_content_type.model_class() is PageCloudinaryFilesGallery
            )
            assert item.item_type == 'file'
            assert item.get_collection_class() is PageCloudinaryFilesGallery
            assert (
                item.get_itemtype_field()
                is PageCloudinaryFilesGallery.item_types['file']
            )

            # FilePreviewItemMixin
            assert item.preview_url == "/static/paper_uploads/dist/image/xls.svg"
            assert item.get_preview_url() == item.preview_url

            # CloudinaryFileItem
            assert item.display_name == 'sheet'

            # as_dict
            assert item.as_dict() == {
                'id': item.pk,
                'name': item.name,
                'extension': item.extension,
                'size': item.size,
                'url': item.get_file_url(),
                'collectionId': item.collection_id,
                'item_type': item.item_type,
                'caption': item.get_basename(),
                'preview': loader.render_to_string(
                    'paper_uploads/collection_item/preview/file.html',
                    {
                        'item': item,
                        'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                        'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                    },
                ),
            }
        finally:
            item.delete_file()
            assert item.is_file_exists() is False

            collection.delete()


class TestCloudinaryMediaItem:
    def test_file_support(self):
        item = CloudinaryMediaItem()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is False

        with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is False

        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            assert (
                item.file_supported(File(pdf_file, name='Sample Document.PDF')) is False
            )

        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is True

    def test_file_item(self):
        collection = PageCloudinaryFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
            item = CloudinaryMediaItem()
            # item.attach_file(xls_file)      # <- works
            item.attach_to(collection)
            item.attach_file(audio_file)  # <- works too
            item.full_clean()
            item.save()

        try:
            # Resource
            assert item.name == 'audio'
            assert now() - item.created_at < timedelta(seconds=10)
            assert now() - item.uploaded_at < timedelta(seconds=10)
            assert now() - item.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert item.hash == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'

            # FileResource
            assert item.extension == 'ogg'
            assert item.size == 105243
            assert str(item) == 'audio.ogg'
            assert repr(item) == "CloudinaryMediaItem('audio.ogg')"
            assert item.get_basename() == 'audio.ogg'
            assert item.get_file() is item.file
            assert re.fullmatch(r'audio_\w+\.ogg', item.get_file_name()) is not None
            assert (
                re.fullmatch(
                    r'http://res\.cloudinary\.com/[^/]+/video/upload/[^/]+/audio_\w+\.ogg',
                    item.get_file_url(),
                )
                is not None
            )
            assert item.is_file_exists() is True

            # ReadonlyFileProxyMixin
            assert item.url == item.get_file_url()

            with pytest.raises(AttributeError):
                print(item.path)

            assert item.closed is True
            with item.open():
                assert item.closed is False
                assert item.read(4) == b'OggS'
                assert item.tell() == 4
                item.seek(0)
                assert item.tell() == 0
                assert item.closed is False
            assert item.closed is True

            # CloudinaryFileResource
            assert item.cloudinary_resource_type == 'video'
            assert item.cloudinary_type == 'upload'

            cloudinary_field = item._meta.get_field('file')
            assert cloudinary_field.type == item.cloudinary_type
            assert cloudinary_field.resource_type == item.cloudinary_resource_type

            item.refresh_from_db()
            assert re.fullmatch(r'audio_\w+', item.get_public_id()) is not None

            # CollectionResourceItem
            assert (
                item.change_form_class
                == 'paper_uploads.forms.dialogs.collection.FileItemDialog'
            )
            assert item.admin_template_name == 'paper_uploads/collection_item/file.html'
            assert item.collection_id == collection.pk
            assert (
                item.collection_content_type.model_class() is PageCloudinaryFilesGallery
            )
            assert item.item_type == 'media'
            assert item.get_collection_class() is PageCloudinaryFilesGallery
            assert (
                item.get_itemtype_field()
                is PageCloudinaryFilesGallery.item_types['media']
            )

            # FilePreviewItemMixin
            assert item.preview_url == "/static/paper_uploads/dist/image/audio.svg"
            assert item.get_preview_url() == item.preview_url

            # CloudinaryMediaItem
            assert item.display_name == 'audio'

            # as_dict
            assert item.as_dict() == {
                'id': item.pk,
                'name': item.name,
                'extension': item.extension,
                'size': item.size,
                'url': item.get_file_url(),
                'collectionId': item.collection_id,
                'item_type': item.item_type,
                'caption': item.get_basename(),
                'preview': loader.render_to_string(
                    'paper_uploads/collection_item/preview/file.html',
                    {
                        'item': item,
                        'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                        'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                    },
                ),
            }
        finally:
            item.delete_file()
            assert item.is_file_exists() is False

            collection.delete()


class TestCloudinaryImageItem:
    def test_file_support(self):
        item = CloudinaryImageItem()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is True

        with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            assert (
                item.file_supported(File(pdf_file, name='Sample Document.PDF')) is False
            )

        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is False

    def test_file_item(self):
        collection = PageCloudinaryFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            item = CloudinaryImageItem(
                title='Image title',
                description='Image description',
            )

            with pytest.raises(AttributeError):
                item.attach_file(File(jpeg_file, name='Image.Jpeg'))

            item.attach_to(collection)
            item.attach_file(jpeg_file)
            item.full_clean()
            item.save()

        try:
            # Resource
            assert item.name == 'Image'
            assert now() - item.created_at < timedelta(seconds=10)
            assert now() - item.uploaded_at < timedelta(seconds=10)
            assert now() - item.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert item.hash == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'

            # FileResource
            assert item.extension == 'jpg'
            assert item.size == 214779
            assert str(item) == 'Image.jpg'
            assert repr(item) == "CloudinaryImageItem('Image.jpg')"
            assert item.get_basename() == 'Image.jpg'
            assert item.get_file() is item.file
            assert re.fullmatch(r'Image_\w+.jpg', item.get_file_name()) is not None
            assert (
                re.fullmatch(
                    r'http://res\.cloudinary\.com/[^/]+/image/upload/[^/]+/Image_\w+\.jpg',
                    item.get_file_url(),
                )
                is not None
            )
            assert item.is_file_exists() is True

            # ReadonlyFileProxyMixin
            assert item.url == item.get_file_url()

            with pytest.raises(AttributeError):
                print(item.path)

            assert item.closed is True
            with item.open():
                assert item.closed is False
                assert item.read(4) == b'\xff\xd8\xff\xe0'
                assert item.tell() == 4
                item.seek(0)
                assert item.tell() == 0
                assert item.closed is False
            assert item.closed is True

            # ImageFileResourceMixin
            assert item.title == 'Image title'
            assert item.description == 'Image description'
            assert item.width == 1600
            assert item.height == 1200
            assert item.cropregion == ''

            # CloudinaryFileResource
            assert item.cloudinary_resource_type == 'image'
            assert item.cloudinary_type == 'upload'

            cloudinary_field = item._meta.get_field('file')
            assert cloudinary_field.type == item.cloudinary_type
            assert cloudinary_field.resource_type == item.cloudinary_resource_type

            item.refresh_from_db()
            assert re.fullmatch(r'Image_\w+', item.get_public_id()) is not None

            # CollectionResourceItem
            assert (
                item.change_form_class
                == 'paper_uploads.forms.dialogs.collection.ImageItemDialog'
            )
            assert (
                item.admin_template_name
                == 'paper_uploads_cloudinary/collection_item/image.html'
            )
            assert item.collection_id == collection.pk
            assert (
                item.collection_content_type.model_class() is PageCloudinaryFilesGallery
            )
            assert item.item_type == 'image'
            assert item.get_collection_class() is PageCloudinaryFilesGallery
            assert (
                item.get_itemtype_field()
                is PageCloudinaryFilesGallery.item_types['image']
            )

            # as_dict
            assert item.as_dict() == {
                'id': item.pk,
                'name': item.name,
                'extension': item.extension,
                'size': item.size,
                'url': item.get_file_url(),
                'collectionId': item.collection_id,
                'item_type': item.item_type,
                'caption': item.get_basename(),
                'width': item.width,
                'height': item.height,
                'cropregion': item.cropregion,
                'title': item.title,
                'description': item.description,
                'preview': loader.render_to_string(
                    'paper_uploads_cloudinary/collection_item/preview/image.html',
                    {
                        'item': item,
                        'preview_width': settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                        'preview_height': settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                    },
                ),
            }
        finally:
            item.delete_file()
            assert item.is_file_exists() is False

            collection.delete()


class TestCollectionField:
    def test_rel(self):
        field = CollectionField(PageCloudinaryGallery)
        assert field.null is True
        assert field.blank is True
        assert field.related_model is PageCloudinaryGallery

    def test_validators(self):
        field = CollectionField(
            PageCloudinaryGallery,
            validators=[
                validators.SizeValidator(10 * 1024 * 1024),
                validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
            ],
        )
        field.contribute_to_class(Page, 'cloud_gallery')

        assert field.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ['image/*'],
        }
