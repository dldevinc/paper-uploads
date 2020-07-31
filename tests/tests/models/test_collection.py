import os
from typing import Tuple

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.template.loader import render_to_string
from django.utils.timezone import now

from app.models import (
    ChildFileCollection,
    CompleteCollection,
    FileCollection,
    IsolatedFileCollection,
)
from paper_uploads.helpers import _get_item_types
from paper_uploads.models import Collection, FileItem, ImageCollection, ImageItem, SVGItem

from ..dummy import *


@pytest.fixture(scope='class')
def collections(class_scoped_db):
    with make_collection(images=False) as collection1:
        with make_collection(extra_file=False, svg=False) as collection2:
            yield collection1, collection2


@pytest.fixture(scope='class')
def complete_collection(class_scoped_db):
    collection = CompleteCollection()
    collection.save()
    yield collection
    collection.delete()


@pytest.fixture(scope='class')
def file_item(class_scoped_db, complete_collection):
    resource = FileItem()
    resource.attach_to(complete_collection)
    with open(CALLIPHORA_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield resource

    resource.delete_file()
    resource.delete()


@pytest.fixture(scope='class')
def image_item(class_scoped_db, complete_collection):
    resource = ImageItem()
    resource.attach_to(complete_collection)
    with open(NATURE_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield resource

    resource.delete_file()
    resource.delete()


@pytest.fixture(scope='class')
def svg_item(class_scoped_db, complete_collection):
    resource = SVGItem()
    resource.attach_to(complete_collection)
    with open(MEDITATION_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield resource

    resource.delete_file()
    resource.delete()


@pytest.mark.django_db
class TestCollectionMetaclass:
    def test_proxy_state(self):
        assert FileCollection._meta.proxy is True
        assert FileCollection._meta.proxy_for_model is Collection

        assert CompleteCollection._meta.proxy is True
        assert CompleteCollection._meta.proxy_for_model is Collection

    def test_explicit_non_proxy(self):
        assert IsolatedFileCollection._meta.proxy is False

    def test_child_collection_proxy_state(self):
        assert ChildFileCollection._meta.proxy is True
        assert ChildFileCollection._meta.proxy_for_model is IsolatedFileCollection

    def test_defined_item_types(self):
        collection_types = _get_item_types(Collection)
        assert collection_types == {}

        image_collection_types = _get_item_types(ImageCollection)
        assert list(image_collection_types.keys()) == ['image']

        file_collection_types = _get_item_types(FileCollection)
        assert list(file_collection_types.keys()) == ['file']

        isolated_collection_types = _get_item_types(IsolatedFileCollection)
        assert list(isolated_collection_types.keys()) == ['file']

        child_collection_types = _get_item_types(ChildFileCollection)
        assert list(child_collection_types.keys()) == ['image', 'svg']

        complete_collection_types = _get_item_types(CompleteCollection)
        assert list(complete_collection_types.keys()) == ['image', 'svg', 'file']

    def test_item_types(self):
        assert Collection.item_types == {}
        assert list(ImageCollection.item_types.keys()) == ['image']
        assert list(FileCollection.item_types.keys()) == ['file']
        assert list(IsolatedFileCollection.item_types.keys()) == ['file']
        assert list(ChildFileCollection.item_types.keys()) == ['image', 'svg']
        assert list(ChildFileCollection.item_types.keys()) == ['image', 'svg']
        assert list(CompleteCollection.item_types.keys()) == ['image', 'svg', 'file']


@pytest.mark.django_db
class TestCollecttion:
    def test_items(self, collections: Tuple[Collection, Collection]):
        c1, c2 = collections
        assert c1.items.count() == 3
        assert c2.items.count() == 2

    def test_get_items(self, collections: Tuple[Collection, Collection]):
        c1, c2 = collections
        assert c1.get_items('file').count() == 2
        assert c2.get_items('file').count() == 1

        assert c1.get_items('image').count() == 0
        assert c2.get_items('image').count() == 1

        assert c1.get_items('svg').count() == 1
        assert c2.get_items('svg').count() == 0

    def test_unsupported_item_type(self):
        collection = FileCollection()
        collection.get_items('file')  # success
        with pytest.raises(ValueError):
            collection.get_items('image')

    def test_collection_id(self, collections: Tuple[Collection, Collection]):
        c1, c2 = collections
        for item1 in c1.get_items():
            assert item1.collection_id == 1
        for item2 in c2.get_items():
            assert item2.collection_id == 2

    def test_manager(self, collections):
        assert CompleteCollection.objects.count() == 2
        assert Collection.objects.count() == 0

    def test_get_collection_class(self, collections):
        files = FileItem.objects.all()
        for file_item in files:
            assert file_item.get_collection_class() is CompleteCollection

    def test_get_itemtype_field(self, collections: Tuple[Collection, Collection]):
        c1, c2 = collections
        image_item = c2.get_items('image').first()
        assert image_item.get_itemtype_field() is CompleteCollection.item_types['image']

        svg_item = c1.get_items('svg').first()
        assert svg_item.get_itemtype_field() is CompleteCollection.item_types['svg']

    def test_attach_to(self, complete_collection):
        file_item = FileItem()
        file_item.attach_to(complete_collection)

        assert file_item.collection_id == complete_collection.pk
        assert file_item.collection_content_type == ContentType.objects.get_for_model(
            CompleteCollection, for_concrete_model=False)
        assert file_item.item_type == 'file'

    def test_get_preview_url(self):
        file_item = FileItem(extension='pdf')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/image/pdf.svg'

        file_item = FileItem(extension='mp4')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/image/mp4.svg'

        file_item = FileItem(extension='docx')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/image/doc.svg'

        file_item = FileItem(extension='ogg')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/image/audio.svg'

        file_item = FileItem(extension='py')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/image/unknown.svg'


@pytest.mark.django_db
class TestFileItem:
    def test_name(self, file_item):
        assert file_item.name == 'calliphora'

    def test_display_name(self, file_item):
        assert file_item.display_name == 'calliphora'

    def test_extension(self, file_item):
        assert file_item.extension == 'jpg'

    def test_size(self, file_item):
        assert file_item.size == 254766

    def test_content_hash(self, file_item):
        assert file_item.content_hash == 'd4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386'

    def test_file_exists(self, file_item):
        assert file_item.file_exists() is True

    def test_get_basename(self, file_item):
        assert file_item.get_basename() == 'calliphora.jpg'

    def test_get_file_name(self, file_item):
        date = now().date().strftime('%Y-%m-%d')
        assert file_item.get_file_name() == 'collections/files/{}/calliphora.jpg'.format(date)

    def test_get_file_url(self, file_item):
        date = now().date().strftime('%Y-%m-%d')
        assert file_item.get_file_url() == '/media/collections/files/{}/calliphora.jpg'.format(date)

    def test_as_dict(self, file_item):
        date = now().date().strftime('%Y-%m-%d')
        assert file_item.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'item_type': 'file',
            'name': 'calliphora',
            'caption': 'calliphora.jpg',
            'extension': 'jpg',
            'size': 254766,
            'url': '/media/collections/files/{}/calliphora.jpg'.format(date),
            'preview': render_to_string(
                'paper_uploads/collection_item/preview/file.html',
                file_item.get_preview_context()
            )
        }

    def test_file_supported(self):
        file_item = FileItem()
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert file_item.file_supported(File(fp)) is True

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert file_item.file_supported(File(fp)) is True

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert file_item.file_supported(File(fp)) is True


@pytest.mark.django_db
class TestFileItemFilesExists:
    def test_files(self, file_item):
        source_path = file_item.path
        assert os.path.exists(source_path) is True
        file_item.delete_file()
        assert os.path.exists(source_path) is False


@pytest.mark.django_db
class TestImageItem:
    def test_name(self, image_item):
        assert image_item.name == 'nature'

    def test_extension(self, image_item):
        assert image_item.extension == 'jpeg'

    def test_size(self, image_item):
        assert image_item.size == 672759

    def test_content_hash(self, image_item):
        assert image_item.content_hash == 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'

    def test_file_exists(self, image_item):
        assert image_item.file_exists() is True

    def test_get_basename(self, image_item):
        assert image_item.get_basename() == 'nature.jpeg'

    def test_get_file_name(self, image_item):
        date = now().date().strftime('%Y-%m-%d')
        assert image_item.get_file_name() == 'collections/images/{}/nature.jpeg'.format(date)

    def test_get_file_url(self, image_item):
        date = now().date().strftime('%Y-%m-%d')
        assert image_item.get_file_url() == '/media/collections/images/{}/nature.jpeg'.format(date)

    def test_width(self, image_item):
        assert image_item.width == 1534

    def test_height(self, image_item):
        assert image_item.height == 2301

    def test_as_dict(self, image_item):
        date = now().date().strftime('%Y-%m-%d')
        assert image_item.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'item_type': 'image',
            'name': 'nature',
            'extension': 'jpg',
            'caption': 'nature.jpg',
            'size': 672759,
            'url': '/media/collections/images/{}/nature.jpeg'.format(date),
            'width': 1534,
            'height': 2301,
            'cropregion': '',
            'title': '',
            'description': '',
            'preview': render_to_string(
                'paper_uploads/collection_item/preview/image.html',
                image_item.get_preview_context()
            )
        }

    def test_file_supported(self):
        image_item = ImageItem()
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert image_item.file_supported(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert image_item.file_supported(File(fp)) is True

        # svg have `image/*` mimetype
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert image_item.file_supported(File(fp)) is True


@pytest.mark.django_db
class TestImageItemFilesExists:
    def test_files(self, image_item):
        source_path = image_item.path
        desktop_path = image_item.desktop.path
        mobile_path = image_item.mobile.path

        assert os.path.exists(source_path) is True
        assert os.path.exists(desktop_path) is True
        assert os.path.exists(mobile_path) is True

        image_item.delete_file()

        assert os.path.exists(source_path) is False
        assert os.path.exists(desktop_path) is False
        assert os.path.exists(mobile_path) is False


@pytest.mark.django_db
class TestSVGItem:
    def test_name(self, svg_item):
        assert svg_item.name == 'Meditation'

    def test_display_name(self, svg_item):
        assert svg_item.display_name == 'Meditation'

    def test_extension(self, svg_item):
        assert svg_item.extension == 'svg'

    def test_size(self, svg_item):
        assert svg_item.size == 47193

    def test_content_hash(self, svg_item):
        assert svg_item.content_hash == '7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d'

    def test_file_exists(self, svg_item):
        assert svg_item.file_exists() is True

    def test_get_basename(self, svg_item):
        assert svg_item.get_basename() == 'Meditation.svg'

    def test_get_file_name(self, svg_item):
        date = now().date().strftime('%Y-%m-%d')
        assert svg_item.get_file_name() == 'collections/files/{}/Meditation.svg'.format(date)

    def test_get_file_url(self, svg_item):
        date = now().date().strftime('%Y-%m-%d')
        assert svg_item.get_file_url() == '/media/collections/files/{}/Meditation.svg'.format(date)

    def test_as_dict(self, svg_item):
        date = now().date().strftime('%Y-%m-%d')
        assert svg_item.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'item_type': 'svg',
            'name': 'Meditation',
            'caption': 'Meditation.svg',
            'extension': 'svg',
            'size': 47193,
            'url': '/media/collections/files/{}/Meditation.svg'.format(date),
            'preview': render_to_string(
                'paper_uploads/collection_item/preview/svg.html',
                svg_item.get_preview_context()
            )
        }

    def test_file_supported(self):
        svg_item = SVGItem()
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert svg_item.file_supported(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert svg_item.file_supported(File(fp)) is False

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert svg_item.file_supported(File(fp)) is True


@pytest.mark.django_db
class TestSVGItemFilesExists:
    def test_files(self, svg_item):
        source_path = svg_item.path
        assert os.path.exists(source_path) is True
        svg_item.delete_file()
        assert os.path.exists(source_path) is False
