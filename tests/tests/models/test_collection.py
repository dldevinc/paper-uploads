import os
import posixpath
from contextlib import contextmanager

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.template.loader import render_to_string

from app.models import (
    ChildFileCollection,
    CompleteCollection,
    CustomGallery,
    CustomImageItem,
    FileCollection,
    IsolatedFileCollection,
    PhotoCollection,
)
from paper_uploads.helpers import _get_item_types
from paper_uploads.models import Collection, FileItem, ImageCollection, ImageItem, SVGItem

from .. import utils
from ..dummy import *
from .test_base import (
    TestFileFieldResource,
    TestFileFieldResourceAttach,
    TestFileFieldResourceDelete,
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
    TestImageAttach,
    TestImageDelete,
    TestImageEmpty,
    TestImageRename,
)


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

        photo_collection_types = _get_item_types(PhotoCollection)
        assert list(photo_collection_types.keys()) == []

        isolated_collection_types = _get_item_types(IsolatedFileCollection)
        assert list(isolated_collection_types.keys()) == ['file']

        child_collection_types = _get_item_types(ChildFileCollection)
        assert list(child_collection_types.keys()) == ['image', 'svg']

        complete_collection_types = _get_item_types(CompleteCollection)
        assert list(complete_collection_types.keys()) == ['svg', 'image', 'file']

    def test_item_types(self):
        assert Collection.item_types == {}
        assert list(ImageCollection.item_types.keys()) == ['image']
        assert list(PhotoCollection.item_types.keys()) == ['image']
        assert list(FileCollection.item_types.keys()) == ['file']
        assert list(IsolatedFileCollection.item_types.keys()) == ['file']
        assert list(ChildFileCollection.item_types.keys()) == ['image', 'svg']
        assert list(ChildFileCollection.item_types.keys()) == ['image', 'svg']
        assert list(CompleteCollection.item_types.keys()) == ['svg', 'image', 'file']


class TestCollection:
    @staticmethod
    def init_class(storage):
        # collection #1 (files only)
        storage.file_collection = FileCollection.objects.create()

        # collection #2 (images only)
        storage.image_collection = PhotoCollection.objects.create()

        # collection #3 (all types allowed)
        storage.global_collection = CompleteCollection.objects.create()

        file_item = FileItem()
        file_item.attach_to(storage.file_collection)
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            file_item.attach_file(fp, name='file_c1.pdf')
        file_item.save()

        image_item = ImageItem()
        image_item.attach_to(storage.image_collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            image_item.attach_file(fp, name='image_c2.jpg')
        image_item.save()

        file_item = FileItem()
        file_item.attach_to(storage.global_collection)
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            file_item.attach_file(fp, name='file_c3.jpg')
        file_item.save()

        image_item = ImageItem()
        image_item.attach_to(storage.global_collection)
        with open(NASA_FILEPATH, 'rb') as fp:
            image_item.attach_file(fp, name='image_c3.jpg')
        image_item.save()

        svg_item = SVGItem()
        svg_item.attach_to(storage.global_collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            svg_item.attach_file(fp, name='svg_c3.svg')
        svg_item.save()

        yield

        for collection in {
            storage.file_collection,
            storage.image_collection,
            storage.global_collection
        }:
            for c_item in collection.items.all():
                c_item.delete_file()
                c_item.delete()
            collection.delete()

    def test_items(self, storage):
        assert storage.file_collection.items.count() == 1
        assert storage.image_collection.items.count() == 1
        assert storage.global_collection.items.count() == 3

    def test_order(self, storage):
        order_values = storage.global_collection.items.values_list('order', flat=True)
        assert sorted(order_values) == [0, 1, 2]

    def test_get_order(self, storage):
        image_item = storage.global_collection.get_items('image').first()
        assert image_item.get_order() == 3

    def test_get_items(self, storage):
        assert storage.file_collection.get_items('file').count() == 1
        assert storage.global_collection.get_items('file').count() == 1

        assert storage.image_collection.get_items('image').count() == 1
        assert storage.global_collection.get_items('image').count() == 1

        assert storage.global_collection.get_items('svg').count() == 1

    def test_get_unsupported_items(self, storage):
        with pytest.raises(ValueError):
            storage.file_collection.get_items('image')

        with pytest.raises(ValueError):
            storage.image_collection.get_items('file')

        with pytest.raises(ValueError):
            storage.global_collection.get_items('nothing')

    def test_collection_id(self, storage):
        for item1 in storage.file_collection.get_items():
            assert item1.collection_id == 1

        for item2 in storage.image_collection.get_items():
            assert item2.collection_id == 2

        for item3 in storage.global_collection.get_items():
            assert item3.collection_id == 3

    def test_manager(self, storage):
        assert Collection.objects.count() == 0
        assert FileCollection.objects.count() == 1
        assert PhotoCollection.objects.count() == 1
        assert CompleteCollection.objects.count() == 1

    def test_get_collection_class(self, storage):
        file1, file2 = FileItem.objects.order_by('id')
        assert file1.get_collection_class() is FileCollection
        assert file2.get_collection_class() is CompleteCollection

    def test_get_itemtype_field(self, storage):
        image_item1 = storage.image_collection.get_items('image').first()
        assert image_item1.get_itemtype_field() is PhotoCollection.item_types['image']

        image_item2 = storage.global_collection.get_items('image').first()
        assert image_item2.get_itemtype_field() is CompleteCollection.item_types['image']

        svg_item = storage.global_collection.get_items('svg').first()
        assert svg_item.get_itemtype_field() is CompleteCollection.item_types['svg']

    def test_attach_to_file_collection(self, storage):
        file_item = FileItem()
        file_item.attach_to(storage.file_collection)

        assert file_item.collection_id == storage.file_collection.pk
        assert file_item.collection_content_type == ContentType.objects.get_for_model(
            FileCollection, for_concrete_model=False)
        assert file_item.item_type == 'file'

    def test_attach_to_global_collection(self, storage):
        file_item = FileItem()
        file_item.attach_to(storage.global_collection)

        assert file_item.collection_id == storage.global_collection.pk
        assert file_item.collection_content_type == ContentType.objects.get_for_model(
            CompleteCollection, for_concrete_model=False)
        assert file_item.item_type == 'file'

    def test_get_preview_url(self):
        file_item = FileItem(extension='pdf')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/assets/pdf.svg'

        file_item = FileItem(extension='mp4')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/assets/mp4.svg'

        file_item = FileItem(extension='docx')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/assets/doc.svg'

        file_item = FileItem(extension='ogg')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/assets/audio.svg'

        file_item = FileItem(extension='py')
        assert file_item.get_preview_url() == '/static/paper_uploads/dist/assets/unknown.svg'

    def test_detect_item_type(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            file = File(fp)
            assert next(storage.file_collection.detect_item_type(file)) == 'file'

        with open(NATURE_FILEPATH, 'rb') as fp:
            file = File(fp)
            assert next(storage.image_collection.detect_item_type(file)) == 'image'

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            file = File(fp)
            assert next(storage.global_collection.detect_item_type(file)) == 'svg'

    def test_detect_item_type_unsupported(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            file = File(fp)
            with pytest.raises(StopIteration):
                next(storage.image_collection.detect_item_type(file))

    def test_svg_detects_as_image(self, storage):
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            file = File(fp)
            assert next(storage.image_collection.detect_item_type(file)) == 'image'


@pytest.mark.django_db
class TestDeleteCollection:
    def _create_collection(self):
        collection = CustomGallery.objects.create()

        image_item = CustomImageItem()
        image_item.attach_to(collection)
        with open(NASA_FILEPATH, 'rb') as fp:
            image_item.attach_file(fp, name='image_del.jpg')
        image_item.save()

        return collection

    def test_explicit_deletion(self):
        collection = self._create_collection()
        collection.delete()

    def test_sql_deletion(self):
        collection = self._create_collection()
        CustomGallery.objects.filter(pk=collection.pk).delete()


class CollectionItemMixin:
    owner_app_label = ''
    owner_model_name = ''
    owner_fieldname = ''
    owner_class = None
    collection_class = None

    def test_item_type(self, storage):
        raise NotImplementedError

    def test_get_owner_model(self, storage):
        # Collection items does not have owner
        assert storage.resource.get_owner_model() is None

    def test_get_owner_field(self, storage):
        # Collection items does not have owner
        assert storage.resource.get_owner_field() is None

    def test_collection_content_type(self, storage):
        assert storage.resource.collection_content_type == ContentType.objects.get_for_model(
            self.collection_class,
            for_concrete_model=False
        )

    def test_get_collection_class(self, storage):
        assert storage.resource.get_collection_class() is self.collection_class

    def test_collection_id(self, storage):
        assert storage.resource.collection_id == storage.collection.pk

    def test_get_order(self, storage):
        assert storage.resource.get_order() == 1

    def test_order(self, storage):
        assert storage.resource.order == 0

    def test_get_caption(self, storage):
        assert storage.resource.get_caption() == '{}.{}'.format(
            self.resource_name,  # noqa: F821
            self.resource_extension  # noqa: F821
        )

    def test_file_supported(self, storage):
        raise NotImplementedError


@pytest.mark.django_db
class TestAttachWrongItemClassToCollection:
    def test_attach(self):
        collection = PhotoCollection.objects.create()
        resource = FileItem()

        with pytest.raises(TypeError):
            resource.attach_to(collection)

        collection.delete()


class TestFileItem(CollectionItemMixin, TestFileFieldResource):
    resource_url = '/media/collections/files/%Y-%m-%d'
    resource_location = 'collections/files/%Y-%m-%d'
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    file_field_name = 'file'
    collection_class = FileCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = FileItem()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_item_type(self, storage):
        assert storage.resource.item_type == 'file'

    def test_get_preview_url(self, storage):
        assert storage.resource.get_preview_url() == '/static/paper_uploads/dist/assets/jpg.svg'

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'itemType': 'file',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'caption': '{}.{}'.format(self.resource_name, self.resource_extension),
            'order': 0,
            'preview': render_to_string(
                'paper_uploads/items/preview/file.html',
                storage.resource.get_preview_context()
            ),
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_file_supported(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is True

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is True

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is True


@pytest.mark.django_db
class TestFileItemAttach(TestFileFieldResourceAttach):
    resource_class = FileItem
    collection_class = CompleteCollection

    @contextmanager
    def get_resource(self):
        collection = self.collection_class.objects.create()
        resource = self.resource_class()
        resource.attach_to(collection)
        try:
            yield resource
        finally:
            resource.delete_file()
            collection.delete()


class TestFileItemRename(TestFileFieldResourceRename):
    resource_class = FileItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = FileCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.rename_file('new_name.png')

        yield

        os.remove(storage.old_source_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestFileItemDelete(TestFileFieldResourceDelete):
    resource_class = FileItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = FileCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.delete_file()

        yield

        storage.resource.delete()


class TestFileItemEmpty(TestFileFieldResourceEmpty):
    recource_class = FileItem
    collection_class = FileCollection

    @classmethod
    def init_class(cls, storage):
        collection = cls.collection_class.objects.create()
        storage.resource = cls.recource_class()
        storage.resource.attach_to(collection)
        yield
        collection.delete()


class TestFileItemExists:
    @staticmethod
    def init_class(storage):
        storage.collection = FileCollection.objects.create()

        storage.resource = FileItem()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        try:
            storage.resource.delete_file()
        except ValueError:
            pass

        storage.resource.delete()
        storage.collection.delete()

    def test_files(self, storage):
        source_path = storage.resource.path
        assert os.path.exists(source_path) is True
        storage.resource.delete_file()
        assert os.path.exists(source_path) is False


class TestSVGItem(CollectionItemMixin, TestFileFieldResource):
    resource_url = '/media/collections/files/%Y-%m-%d'
    resource_location = 'collections/files/%Y-%m-%d'
    resource_name = 'Meditation'
    resource_extension = 'svg'
    resource_size = 47193
    resource_checksum = '7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d'
    owner_app_label = ''
    owner_model_name = ''
    owner_fieldname = ''
    owner_class = None
    file_field_name = 'file'
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = SVGItem()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_item_type(self, storage):
        assert storage.resource.item_type == 'svg'

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'Meditation{suffix}.svg')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        pattern = posixpath.join(self.resource_url, 'Meditation{suffix}.svg')
        assert file_url == utils.get_target_filepath(pattern, file_url)

    def test_path(self, storage):
        path = storage.resource.path
        pattern = posixpath.join('media', self.resource_location, 'Meditation{suffix}.svg')
        assert path.endswith(utils.get_target_filepath(pattern, path))

    def test_url(self, storage):
        url = storage.resource.url
        pattern = posixpath.join(self.resource_url, 'Meditation{suffix}.svg')
        assert url == utils.get_target_filepath(pattern, url)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'itemType': 'svg',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'caption': '{}.{}'.format(self.resource_name, self.resource_extension),
            'order': 0,
            'preview': render_to_string(
                'paper_uploads/items/preview/svg.html',
                storage.resource.get_preview_context()
            ),
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(5) == b'<?xml'

    def test_file_supported(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is False

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is False


@pytest.mark.django_db
class TestSVGItemAttach(TestFileFieldResourceAttach):
    resource_class = SVGItem
    collection_class = CompleteCollection

    @contextmanager
    def get_resource(self):
        collection = self.collection_class.objects.create()
        resource = self.resource_class()
        resource.attach_to(collection)
        try:
            yield resource
        finally:
            resource.delete_file()
            collection.delete()


class TestSVGItemRename(TestFileFieldResourceRename):
    resource_class = SVGItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.rename_file('new_name.png')

        yield

        os.remove(storage.old_source_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestSVGItemDelete(TestFileFieldResourceDelete):
    resource_class = SVGItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.delete_file()

        yield

        storage.resource.delete()


class TestSVGItemEmpty(TestFileFieldResourceEmpty):
    recource_class = SVGItem
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        collection = cls.collection_class.objects.create()
        storage.resource = cls.recource_class()
        storage.resource.attach_to(collection)
        yield
        collection.delete()


class TestSVGItemExists:
    @classmethod
    def init_class(cls, storage):
        storage.collection = CompleteCollection.objects.create()

        storage.resource = SVGItem()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        try:
            storage.resource.delete_file()
        except ValueError:
            pass

        storage.resource.delete()
        storage.collection.delete()

    def test_files(self, storage):
        source_path = storage.resource.path
        assert os.path.exists(source_path) is True
        storage.resource.delete_file()
        assert os.path.exists(source_path) is False


class TestImageItem(CollectionItemMixin, TestFileFieldResource):
    resource_url = '/media/collections/images/%Y-%m-%d'
    resource_location = 'collections/images/%Y-%m-%d'
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = ''
    owner_model_name = ''
    owner_fieldname = ''
    owner_class = None
    file_field_name = 'file'
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = ImageItem()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_item_type(self, storage):
        assert storage.resource.item_type == 'image'

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}.jpg')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        pattern = posixpath.join(self.resource_url, 'Nature_Tree{suffix}.jpg')
        assert file_url == utils.get_target_filepath(pattern, file_url)

    def test_path(self, storage):
        path = storage.resource.path
        pattern = posixpath.join('media', self.resource_location, 'Nature_Tree{suffix}.jpg')
        assert path.endswith(utils.get_target_filepath(pattern, path))

    def test_url(self, storage):
        url = storage.resource.url
        pattern = posixpath.join(self.resource_url, 'Nature_Tree{suffix}.jpg')
        assert url == utils.get_target_filepath(pattern, url)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'itemType': 'image',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'width': 1534,
            'height': 2301,
            'cropregion': '',
            'title': '',
            'description': '',
            'caption': '{}.{}'.format(self.resource_name, self.resource_extension),
            'order': 0,
            'preview': render_to_string(
                'paper_uploads/items/preview/image.html',
                storage.resource.get_preview_context()
            ),
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_get_variations(self, storage):
        variations = storage.resource.get_variations()
        for name in storage.resource.PREVIEW_VARIATIONS:
            assert name in variations

    def test_width(self, storage):
        assert storage.resource.width == 1534

    def test_height(self, storage):
        assert storage.resource.height == 2301

    def test_file_supported(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is True

        # SVG passes image test
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.file_supported(File(fp)) is False


@pytest.mark.django_db
class TestImageItemAttach(TestImageAttach):
    resource_class = ImageItem
    collection_class = CompleteCollection

    @contextmanager
    def get_resource(self):
        collection = self.collection_class.objects.create()
        resource = self.resource_class()
        resource.attach_to(collection)
        try:
            yield resource
        finally:
            resource.delete_file()
            collection.delete()


class TestImageItemRename(TestImageRename):
    resource_class = ImageItem
    resource_location = 'collections/images/%Y-%m-%d'
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_desktop_name = storage.resource.desktop.name
        storage.old_mobile_name = storage.resource.mobile.name

        storage.old_source_path = file.path
        storage.old_desktop_path = storage.resource.desktop.path
        storage.old_mobile_path = storage.resource.mobile.path

        storage.resource.rename_file('new_name.png')

        yield

        os.remove(storage.old_source_path)
        os.remove(storage.old_desktop_path)
        os.remove(storage.old_mobile_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestImageItemDelete(TestImageDelete):
    resource_class = ImageItem
    resource_location = 'collections/images/%Y-%m-%d'
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_desktop_name = storage.resource.desktop.name
        storage.old_mobile_name = storage.resource.mobile.name

        storage.old_source_path = file.path
        storage.old_desktop_path = storage.resource.desktop.path
        storage.old_mobile_path = storage.resource.mobile.path

        storage.resource.delete_file()

        yield

        storage.resource.delete()


class TestImageItemEmpty(TestImageEmpty):
    recource_class = ImageItem
    collection_class = CompleteCollection

    @classmethod
    def init_class(cls, storage):
        collection = cls.collection_class.objects.create()
        storage.resource = cls.recource_class()
        storage.resource.attach_to(collection)
        yield
        collection.delete()


class TestImageItemExists:
    @classmethod
    def init_class(cls, storage):
        storage.collection = CompleteCollection.objects.create()

        storage.resource = ImageItem()
        storage.resource.attach_to(storage.collection)
        with open(NASA_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        try:
            storage.resource.delete_file()
        except ValueError:
            pass

        storage.resource.delete()
        storage.collection.delete()

    def test_files(self, storage):
        source_path = storage.resource.path
        desktop_path = storage.resource.desktop.path
        mobile_path = storage.resource.mobile.path

        assert os.path.exists(source_path) is True
        assert os.path.exists(desktop_path) is True
        assert os.path.exists(mobile_path) is True

        storage.resource.delete_file()

        assert os.path.exists(source_path) is False
        assert os.path.exists(desktop_path) is False
        assert os.path.exists(mobile_path) is False
