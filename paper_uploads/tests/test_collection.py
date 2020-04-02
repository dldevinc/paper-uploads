import os
import re
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.template import loader
from django.utils.timezone import now
from tests.app.models import (
    DummyCollection, DummyCollectionWithMeta, DummyCollectionSubclass,
    Page, PageFilesGallery, PageGallery
)

from .. import validators
from ..conf import settings as paper_settings
from ..models import FileItem, ImageItem, SVGItem, VariationFile
from ..models.fields import CollectionField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestCollection:
    def test_item_types_attribute(self):
        assert list(DummyCollection.item_types.keys()) == ['image']
        assert list(DummyCollectionWithMeta.item_types.keys()) == []
        assert list(DummyCollectionSubclass.item_types.keys()) == ['image', 'svg']

        image_field = DummyCollectionSubclass.item_types['image']
        assert list(image_field.options['variations']) == ['preview']

    def test_collection(self):
        collection = PageFilesGallery.objects.create(
            owner_app_label="app",
            owner_model_name="page",
            owner_fieldname="files",
        )

        try:
            assert collection.item_types.keys() == {'image', 'svg', 'file'}
            assert collection.item_types['image'].model is ImageItem
            assert collection.item_types['svg'].model is SVGItem
            assert collection.item_types['file'].model is FileItem

            with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
                assert (
                    collection.detect_file_type(File(jpeg_file, name='Image.Jpeg'))
                    == 'image'
                )

            with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
                assert (
                    collection.detect_file_type(File(svg_file, name='cartman.svg'))
                    == 'svg'
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
                    == 'file'
                )

            # ReverseFieldModelMixin
            assert collection.owner_app_label == 'app'
            assert collection.owner_model_name == 'page'
            assert collection.owner_fieldname == 'files'
            assert collection.get_owner_model() is Page
            assert collection.get_owner_field() is Page._meta.get_field('files')
        finally:
            collection.delete()

    def test_image_collection(self):
        collection = PageGallery.objects.create(
            owner_app_label="app",
            owner_model_name="page",
            owner_fieldname="gallery",
        )

        try:
            assert collection.item_types.keys() == {'image'}
            assert collection.item_types['image'].model is ImageItem
            assert collection.get_validation() == {'acceptFiles': ['image/*']}

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
            assert collection.owner_fieldname == 'gallery'
            assert collection.get_owner_model() is Page
            assert collection.get_owner_field() is Page._meta.get_field('gallery')
        finally:
            collection.delete()

    def test_manager(self):
        PageFilesGallery.objects.create()
        PageFilesGallery.objects.create()
        PageGallery.objects.create()
        PageGallery.objects.create()
        PageGallery.objects.create()

        assert PageFilesGallery.objects.count() == 2
        assert PageGallery.objects.count() == 3
        assert PageFilesGallery._base_manager.count() == 5
        assert PageGallery._base_manager.count() == 5


class TestFileItem:
    def test_file_support(self):
        item = FileItem()

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
        collection = PageFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'sheet.xlsx'), 'rb') as xls_file:
            item = FileItem()
            # item.attach_file(xls_file)      # <- works
            item.attach_to(collection)
            item.attach_file(xls_file)  # <- works too
            item.full_clean()
            item.save()

        suffix_match = re.match(r"sheet((?:_\w+)?)", os.path.basename(item.file.name))
        assert suffix_match is not None
        suffix = suffix_match.group(1)

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
            assert repr(item) == "FileItem('sheet.xlsx')"
            assert item.get_basename() == 'sheet.xlsx'
            assert item.get_file() is item.file
            assert (
                item.get_file_name() == "collections/files/{}/sheet{}.xlsx".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert (
                item.get_file_url() == "/media/collections/files/{}/sheet{}.xlsx".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert item.is_file_exists() is True

            # FileFieldResource
            assert os.path.isfile(item.path)

            # PostrocessableFileFieldResource
            assert os.stat(str(TESTS_PATH / 'sheet.xlsx')).st_size == 8628629

            # ReadonlyFileProxyMixin
            assert item.url == item.get_file_url()
            assert item.path == os.path.join(
                settings.BASE_DIR, settings.MEDIA_ROOT, item.get_file_name()
            )
            assert item.closed is True
            with item.open():
                assert item.closed is False
                assert item.read(4) == b'PK\x03\x04'
                assert item.tell() == 4
                item.seek(0)
                assert item.tell() == 0
                assert item.closed is False
            assert item.closed is True

            # CollectionResourceItem
            assert (
                item.change_form_class
                == 'paper_uploads.forms.dialogs.collection.FileItemDialog'
            )
            assert item.admin_template_name == 'paper_uploads/collection_item/file.html'
            assert item.collection_id == collection.pk
            assert item.collection_content_type.model_class() is PageFilesGallery
            assert item.item_type == 'file'
            assert item.get_collection_class() is PageFilesGallery
            assert item.get_itemtype_field() is PageFilesGallery.item_types['file']

            # FilePreviewItemMixin
            assert item.preview_url == "/static/paper_uploads/dist/image/xls.svg"
            assert item.get_preview_url() == item.preview_url

            # FileItem
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
                        'preview_width': paper_settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                        'preview_height': paper_settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                    },
                ),
            }
        finally:
            file_path = item.path
            assert os.path.isfile(file_path) is True
            item.delete_file()
            assert os.path.isfile(file_path) is False
            assert item.is_file_exists() is False

            collection.delete()


class TestSVGItem:
    def test_file_support(self):
        item = SVGItem()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            assert item.file_supported(File(jpeg_file, name='Image.Jpeg')) is False

        with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
            assert item.file_supported(File(svg_file, name='cartman.svg')) is True

        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            assert (
                item.file_supported(File(pdf_file, name='Sample Document.PDF')) is False
            )

        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
            assert item.file_supported(File(audio_file, name='audio.ogg')) is False

    def test_svg_item(self):
        collection = PageFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
            item = SVGItem()
            # item.attach_file(svg_file)      # <- works
            item.attach_to(collection)
            item.attach_file(svg_file)  # <- works too
            item.full_clean()
            item.save()

        suffix_match = re.match(r"cartman((?:_\w+)?)", os.path.basename(item.file.name))
        assert suffix_match is not None
        suffix = suffix_match.group(1)

        try:
            # Resource
            assert item.name == 'cartman'
            assert now() - item.created_at < timedelta(seconds=10)
            assert now() - item.uploaded_at < timedelta(seconds=10)
            assert now() - item.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert item.hash == '563bca379c51c21a7bdff080f7cff67914040c10'

            # FileResource
            assert item.extension == 'svg'
            assert item.size == 1118
            assert str(item) == 'cartman.svg'
            assert repr(item) == "SVGItem('cartman.svg')"
            assert item.get_basename() == 'cartman.svg'
            assert item.get_file() is item.file
            assert (
                item.get_file_name() == "collections/files/{}/cartman{}.svg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert (
                item.get_file_url() == "/media/collections/files/{}/cartman{}.svg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert item.is_file_exists() is True

            # FileFieldResource
            assert os.path.isfile(item.path)

            # PostrocessableFileFieldResource
            assert os.stat(str(TESTS_PATH / 'cartman.svg')).st_size == 1183

            # ReadonlyFileProxyMixin
            assert item.url == item.get_file_url()
            assert item.path == os.path.join(
                settings.BASE_DIR, settings.MEDIA_ROOT, item.get_file_name()
            )
            assert item.closed is True
            with item.open():
                assert item.closed is False
                assert item.read(4) == b'<svg'
                assert item.tell() == 4
                item.seek(0)
                assert item.tell() == 0
                assert item.closed is False
            assert item.closed is True

            # CollectionResourceItem
            assert (
                item.change_form_class
                == 'paper_uploads.forms.dialogs.collection.FileItemDialog'
            )
            assert item.admin_template_name == 'paper_uploads/collection_item/svg.html'
            assert item.collection_id == collection.pk
            assert item.collection_content_type.model_class() is PageFilesGallery
            assert item.item_type == 'svg'
            assert item.get_collection_class() is PageFilesGallery
            assert item.get_itemtype_field() is PageFilesGallery.item_types['svg']

            # FileItem
            assert item.display_name == 'cartman'

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
                    'paper_uploads/collection_item/preview/svg.html',
                    {
                        'item': item,
                        'preview_width': paper_settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                        'preview_height': paper_settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                    },
                ),
            }
        finally:
            file_path = item.path
            assert os.path.isfile(file_path) is True
            item.delete_file()
            assert os.path.isfile(file_path) is False
            assert item.is_file_exists() is False

            collection.delete()

    def test_unsupported_file(self):
        collection = PageFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'sheet.xlsx'), 'rb') as svg_file:
            item = SVGItem()
            item.attach_to(collection)
            item.attach_file(svg_file)
            item.full_clean()
            item.save()

        item.delete_file()
        item.delete()
        collection.delete()


class TestImageItem:
    def test_file_support(self):
        item = ImageItem()

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

    def test_image_item(self):
        collection = PageFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'Image.Jpeg'), "rb") as jpeg_file:
            item = ImageItem(
                title="Image title",
                description="Image description",
            )

            # item.attach_file(jpeg_file)     # <- TODO: recursion error
            item.attach_to(collection)
            item.attach_file(jpeg_file)
            item.full_clean()
            item.save()

        suffix_match = re.match(r"Image((?:_\w+)?)", os.path.basename(item.file.name))
        assert suffix_match is not None
        suffix = suffix_match.group(1)

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
            assert repr(item) == "ImageItem('Image.jpg')"
            assert item.get_basename() == 'Image.jpg'
            assert item.get_file() is item.file
            assert (
                item.get_file_name() == "collections/images/{}/Image{}.jpg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert (
                item.get_file_url() == "/media/collections/images/{}/Image{}.jpg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert item.is_file_exists() is True

            # FileFieldResource
            assert os.path.isfile(item.path)
            assert all(
                os.path.isfile(vfile.path) for vname, vfile in item.variation_files()
            )

            # PostrocessableFileFieldResource
            assert os.stat(str(TESTS_PATH / 'Image.Jpeg')).st_size == 214779

            # ReadonlyFileProxyMixin
            assert item.url == item.get_file_url()
            assert item.path == os.path.join(
                settings.BASE_DIR, settings.MEDIA_ROOT, item.get_file_name()
            )
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

            # VariableImageResourceMixin
            assert item.get_variations().keys() == {
                'mobile',
                'admin_preview',
                'admin_preview_2x',
                'admin_preview_webp',
                'admin_preview_webp_2x',
            }

            assert item._variations_attached is False
            assert isinstance(item.get_variation_file('mobile'), VariationFile)
            assert item.mobile is item.get_variation_file('mobile')
            assert item._variations_attached is True

            for vname, vfile in item.variation_files():
                assert isinstance(vfile, VariationFile)
                assert vfile is item.get_variation_file(vname)

            assert item.calculate_max_size((3000, 2000)) == (640, 427)
            assert item.calculate_max_size((1600, 1000)) == (640, 400)
            assert item.calculate_max_size((1400, 1200)) == (640, 549)
            assert item.calculate_max_size((600, 400)) == (640, 400)

            expected_varaition_sizes = {
                'mobile': 39098,
                'admin_preview': 3639,
                'admin_preview_2x': 10171,
                'admin_preview_webp': 2532,
                'admin_preview_webp_2x': 6448,
            }

            for vname, vfile in item.variation_files():
                assert os.path.isfile(vfile.path)
                assert os.stat(vfile.path).st_size == expected_varaition_sizes[vname]

            with pytest.raises(KeyError):
                item.get_variation_file('nothing')

            # CollectionResourceItem
            assert (
                item.change_form_class
                == 'paper_uploads.forms.dialogs.collection.ImageItemDialog'
            )
            assert (
                item.admin_template_name == 'paper_uploads/collection_item/image.html'
            )
            assert item.collection_id == collection.pk
            assert item.collection_content_type.model_class() is PageFilesGallery
            assert item.item_type == 'image'
            assert item.get_collection_class() is PageFilesGallery
            assert item.get_itemtype_field() is PageFilesGallery.item_types['image']

            # ImageItem
            # assert item.display_name == 'Image'

            # as_dict
            assert item.as_dict() == {
                'id': item.pk,
                'name': item.name,
                'extension': item.extension,
                'size': item.size,
                'url': item.get_file_url(),
                'collectionId': item.collection_id,
                'item_type': item.item_type,
                'width': item.width,
                'height': item.height,
                'cropregion': item.cropregion,
                'title': item.title,
                'description': item.description,
                'caption': item.get_basename(),
                'preview': loader.render_to_string(
                    'paper_uploads/collection_item/preview/image.html',
                    {
                        'item': item,
                        'preview_width': paper_settings.COLLECTION_ITEM_PREVIEW_WIDTH,
                        'preview_height': paper_settings.COLLECTION_ITEM_PREVIEW_HEIGTH,
                    },
                ),
            }
        finally:
            source_path = item.path
            variation_pathes = {vfile.path for vname, vfile in item.variation_files()}

            item.delete_file()
            assert os.path.isfile(source_path) is False
            assert all(not os.path.isfile(path) for path in variation_pathes)
            assert item.is_file_exists() is False

            collection.delete()

    def test_unsupported_file(self):
        collection = PageFilesGallery.objects.create()

        with open(str(TESTS_PATH / 'sheet.xlsx'), 'rb') as svg_file:
            item = ImageItem()
            item.attach_to(collection)

            with pytest.raises(ValidationError) as exc:
                item.attach_file(svg_file)
            assert exc.value.message == "`sheet.xlsx` is not an image"

        item.delete_file()
        collection.delete()


class TestCollectionField:
    def test_rel(self):
        field = CollectionField(PageGallery)
        assert field.null is True
        assert field.blank is True
        assert field.related_model is PageGallery

    def test_validators(self):
        field = CollectionField(
            PageGallery,
            validators=[
                validators.SizeValidator(10 * 1024 * 1024),
                validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
            ],
        )
        field.contribute_to_class(Page, 'gallery')

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
