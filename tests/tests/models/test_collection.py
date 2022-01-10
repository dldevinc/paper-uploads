import os
import posixpath
from contextlib import contextmanager

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.template.loader import render_to_string
from examples.custom_collection.models import CustomCollection, CustomSubCollection
from examples.custom_collection_item.models import CustomImageCollection, CustomImageItem
from examples.standard_collection.models import (
    FilesOnlyCollection,
    ImagesOnlyCollection,
    MixedCollection,
    Page,
)
from examples.variations.models import PhotoCollection

from paper_uploads import exceptions
from paper_uploads.conf import IMAGE_ITEM_VARIATIONS
from paper_uploads.helpers import _get_item_types
from paper_uploads.models import Collection, FileItem, ImageCollection, ImageItem, SVGItem

from .. import utils
from ..dummy import *
from .test_dummy import (
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
        assert FilesOnlyCollection._meta.proxy is True
        assert FilesOnlyCollection._meta.proxy_for_model is Collection

        assert ImagesOnlyCollection._meta.proxy is True
        assert ImagesOnlyCollection._meta.proxy_for_model is ImageCollection

        assert MixedCollection._meta.proxy is True
        assert MixedCollection._meta.proxy_for_model is Collection

    def test_explicit_non_proxy(self):
        assert CustomCollection._meta.proxy is False

    def test_child_collection_proxy_state(self):
        assert CustomSubCollection._meta.proxy is True
        assert CustomSubCollection._meta.proxy_for_model is CustomCollection

    def test_declared_item_types(self):
        """
        Проверка классов элементов коллекции, объявленных в самих классах.
        Унаследованные классы не учитываются.
        """
        collection_types = _get_item_types(Collection)
        assert collection_types == {}

        image_collection_types = _get_item_types(ImageCollection)
        assert list(image_collection_types.keys()) == ['image']

        file_collection_types = _get_item_types(FilesOnlyCollection)
        assert list(file_collection_types.keys()) == ['file']

        photo_collection_types = _get_item_types(ImagesOnlyCollection)
        assert list(photo_collection_types.keys()) == []

        custom_collection_types = _get_item_types(CustomCollection)
        assert list(custom_collection_types.keys()) == ['image']

        custom_subcollection_types = _get_item_types(CustomSubCollection)
        assert list(custom_subcollection_types.keys()) == ['svg']

        mixed_collection_types = _get_item_types(MixedCollection)
        assert list(mixed_collection_types.keys()) == ['svg', 'image', 'file']

    def test_item_types(self):
        assert Collection.item_types == {}
        assert list(ImageCollection.item_types.keys()) == ['image']
        assert list(ImagesOnlyCollection.item_types.keys()) == ['image']
        assert list(FilesOnlyCollection.item_types.keys()) == ['file']
        assert list(CustomCollection.item_types.keys()) == ['image']
        assert list(CustomSubCollection.item_types.keys()) == ['image', 'svg']
        assert list(MixedCollection.item_types.keys()) == ['svg', 'image', 'file']


class TestCollection:
    @staticmethod
    def init_class(storage):
        # collection #1 (files only)
        storage.file_collection = FilesOnlyCollection.objects.create()

        # collection #2 (images only)
        storage.image_collection = ImagesOnlyCollection.objects.create()

        # collection #3 (all types allowed)
        storage.global_collection = MixedCollection.objects.create()

        file_item = FileItem()
        file_item.attach_to(storage.file_collection)
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            file_item.attach(fp, name='file_c1.pdf')
        file_item.save()

        image_item = ImageItem()
        image_item.attach_to(storage.image_collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            image_item.attach(fp, name='image_c2.jpg')
        image_item.save()

        file_item = FileItem()
        file_item.attach_to(storage.global_collection)
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            file_item.attach(fp, name='file_c3.jpg')
        file_item.save()

        image_item = ImageItem()
        image_item.attach_to(storage.global_collection)
        with open(NASA_FILEPATH, 'rb') as fp:
            image_item.attach(fp, name='image_c3.jpg')
        image_item.save()

        svg_item = SVGItem()
        svg_item.attach_to(storage.global_collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            svg_item.attach(fp, name='svg_c3.svg')
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

    def test_iter(self, storage):
        iterator = iter(storage.global_collection)
        
        assert isinstance(next(iterator), FileItem)
        assert isinstance(next(iterator), ImageItem)
        assert isinstance(next(iterator), SVGItem)
        
        with pytest.raises(StopIteration):
            next(iterator)

    def test_get_unsupported_items(self, storage):
        with pytest.raises(exceptions.InvalidItemType):
            storage.file_collection.get_items('image')

        with pytest.raises(exceptions.InvalidItemType):
            storage.image_collection.get_items('file')

        with pytest.raises(exceptions.InvalidItemType):
            storage.global_collection.get_items('nothing')

    def test_collection_id(self, storage):
        for item1 in storage.file_collection.get_items():
            assert item1.collection_id == 1

        for item2 in storage.image_collection.get_items():
            assert item2.collection_id == 2

        for item3 in storage.global_collection.get_items():
            assert item3.collection_id == 3

    def test_manager(self, storage):
        assert Collection.objects.count() == 3
        assert FilesOnlyCollection.objects.count() == 1
        assert ImagesOnlyCollection.objects.count() == 1
        assert MixedCollection.objects.count() == 1

    def test_get_collection_class(self, storage):
        file1, file2 = FileItem.objects.order_by('id')
        assert file1.get_collection_class() is FilesOnlyCollection
        assert file2.get_collection_class() is MixedCollection

    def test_get_itemtype_field(self, storage):
        image_item1 = storage.image_collection.get_items('image').first()
        assert image_item1.get_itemtype_field() is ImagesOnlyCollection.item_types['image']

        image_item2 = storage.global_collection.get_items('image').first()
        assert image_item2.get_itemtype_field() is MixedCollection.item_types['image']

        svg_item = storage.global_collection.get_items('svg').first()
        assert svg_item.get_itemtype_field() is MixedCollection.item_types['svg']

    def test_attach_to_file_collection(self, storage):
        file_item = FileItem()
        file_item.attach_to(storage.file_collection)

        assert file_item.collection_id == storage.file_collection.pk
        assert file_item.collection_content_type == ContentType.objects.get_for_model(
            FilesOnlyCollection, for_concrete_model=False)
        assert file_item.type == 'file'

    def test_attach_to_global_collection(self, storage):
        file_item = FileItem()
        file_item.attach_to(storage.global_collection)

        assert file_item.collection_id == storage.global_collection.pk
        assert file_item.collection_content_type == ContentType.objects.get_for_model(
            MixedCollection, for_concrete_model=False)
        assert file_item.type == 'file'

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

    def test_set_owner_from(self, storage):
        owner_field = Page._meta.get_field("file_collection")
        storage.file_collection.set_owner_from(owner_field)
        assert storage.file_collection.owner_app_label == "standard_collection"
        assert storage.file_collection.owner_model_name == "page"
        assert storage.file_collection.owner_fieldname == "file_collection"
        assert storage.file_collection.get_owner_model() is Page
        assert storage.file_collection.get_owner_field() is owner_field

    def test_get_item_model(self, storage):
        assert storage.global_collection.get_item_model("svg") is SVGItem
        assert storage.global_collection.get_item_model("image") is ImageItem
        assert storage.global_collection.get_item_model("file") is FileItem
        with pytest.raises(exceptions.InvalidItemType):
            storage.global_collection.get_item_model("video")


@pytest.mark.django_db
class TestDeleteCustomImageCollection:
    def _create_collection(self):
        collection = CustomImageCollection.objects.create()

        image_item = CustomImageItem()
        image_item.attach_to(collection)
        with open(NASA_FILEPATH, 'rb') as fp:
            image_item.attach(fp, name='image_del.jpg')
        image_item.save()

        return collection

    def test_explicit_deletion(self):
        collection = self._create_collection()
        item = collection.items.first()  # type: CustomImageItem
        item_files = [item.get_file(), *(pair[1] for pair in item.variation_files())]

        collection.delete()

        for vfile in item_files:
            vfile.delete()

    def test_sql_deletion(self):
        collection = self._create_collection()
        item = collection.items.first()  # type: CustomImageItem
        item_files = [item.get_file(), *(pair[1] for pair in item.variation_files())]

        CustomCollection.objects.filter(pk=collection.pk).delete()

        for vfile in item_files:
            vfile.delete()


class CollectionItemMixin:
    collection_class = None

    def test_item_type(self, storage):
        raise NotImplementedError

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

    def test_accept(self, storage):
        raise NotImplementedError


@pytest.mark.django_db
class TestAttachWrongItemClassToCollection:
    def test_attach(self):
        collection = ImagesOnlyCollection.objects.create()
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
    collection_class = FilesOnlyCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = FileItem()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
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
        assert storage.resource.type == 'file'

    def test_get_preview_url(self, storage):
        assert storage.resource.get_preview_url() == '/static/paper_uploads/dist/assets/jpg.svg'

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'itemType': 'file',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'caption': '{}.{}'.format(
                self.resource_name,
                self.resource_extension
            ),
            'size': self.resource_size,
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

    def test_accept(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True


@pytest.mark.django_db
class TestFileItemAttach(TestFileFieldResourceAttach):
    resource_class = FileItem
    collection_class = MixedCollection

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
    collection_class = FilesOnlyCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.rename('new_name.png')
        storage.resource.save()

        yield

        os.remove(storage.old_source_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestFileItemDelete(TestFileFieldResourceDelete):
    resource_class = FileItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = FilesOnlyCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.delete_file()

        yield

        storage.resource.delete()


class TestFileItemEmpty(TestFileFieldResourceEmpty):
    recource_class = FileItem
    collection_class = FilesOnlyCollection

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
        storage.collection = FilesOnlyCollection.objects.create()

        storage.resource = FileItem()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
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
    file_field_name = 'file'
    collection_class = MixedCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = SVGItem()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_item_type(self, storage):
        assert storage.resource.type == 'svg'

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
            'caption': '{}.{}'.format(
                self.resource_name,
                self.resource_extension
            ),
            'size': self.resource_size,
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

    def test_accept(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False


@pytest.mark.django_db
class TestSVGItemAttach(TestFileFieldResourceAttach):
    resource_class = SVGItem
    collection_class = MixedCollection

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
    collection_class = MixedCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.rename('new_name.png')
        storage.resource.save()

        yield

        os.remove(storage.old_source_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestSVGItemDelete(TestFileFieldResourceDelete):
    resource_class = SVGItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = MixedCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.delete_file()

        yield

        storage.resource.delete()


class TestSVGItemEmpty(TestFileFieldResourceEmpty):
    recource_class = SVGItem
    collection_class = MixedCollection

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
        storage.collection = MixedCollection.objects.create()

        storage.resource = SVGItem()
        storage.resource.attach_to(storage.collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
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
    file_field_name = 'file'
    collection_class = PhotoCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = ImageItem()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_item_type(self, storage):
        assert storage.resource.type == 'image'

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
            'caption': '{}.{}'.format(
                self.resource_name,
                self.resource_extension
            ),
            'size': self.resource_size,
            'width': 1534,
            'height': 2301,
            'cropregion': '',
            'title': '',
            'description': '',
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

        assert "desktop" in variations
        assert "mobile" in variations
        assert "admin_preview" in variations

        assert variations["desktop"].size == (800, 0)
        assert variations["mobile"].size == (0, 600)

        # admin variation overriden
        assert variations["admin_preview"].size == (200, 100)
        assert variations["admin_preview"].format == "AUTO"

        # ensure that setting has not changed
        assert ImageItem.PREVIEW_VARIATIONS["admin_preview"]["size"] == (180, 135)
        assert IMAGE_ITEM_VARIATIONS["admin_preview"]["size"] == (180, 135)

    def test_width(self, storage):
        assert storage.resource.width == 1534

    def test_height(self, storage):
        assert storage.resource.height == 2301

    def test_accept(self, storage):
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        # SVG passes image test
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False


@pytest.mark.django_db
class TestImageItemAttach(TestImageAttach):
    resource_class = ImageItem
    collection_class = PhotoCollection

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

    def test_unsupported_file(self):
        resource = self.resource_class()
        with pytest.raises(exceptions.UnsupportedResource):
            with open(AUDIO_FILEPATH, "rb") as fp:
                resource.attach(fp)


class TestImageItemRename(TestImageRename):
    resource_class = ImageItem
    resource_location = 'collections/images/%Y-%m-%d'
    collection_class = PhotoCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_desktop_name = storage.resource.desktop.name
        storage.old_mobile_name = storage.resource.mobile.name
        storage.old_admin_preview_name = storage.resource.admin_preview.name

        storage.old_source_path = file.path
        storage.old_desktop_path = storage.resource.desktop.path
        storage.old_mobile_path = storage.resource.mobile.path
        storage.old_admin_preview_path = storage.resource.admin_preview.path

        storage.resource.rename('new_name.png')
        assert storage.resource.need_recut is True
        storage.resource.save()

        yield

        os.remove(storage.old_source_path)
        os.remove(storage.old_desktop_path)
        os.remove(storage.old_mobile_path)
        os.remove(storage.old_admin_preview_path)
        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_name(self, storage):
        super().test_old_file_name(storage)
        assert storage.old_admin_preview_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.admin_preview.jpg'),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        super().test_new_file_name(storage)
        assert storage.resource.admin_preview.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_name{suffix}.admin_preview.png'),
            storage.resource.file.name
        )

    def test_old_file_exists(self, storage):
        super().test_old_file_exists(storage)
        assert os.path.exists(storage.old_admin_preview_path) is True

    def test_new_file_exists(self, storage):
        super().test_old_file_exists(storage)
        assert os.path.exists(storage.resource.admin_preview.path) is True


class TestImageItemDelete(TestImageDelete):
    resource_class = ImageItem
    resource_location = 'collections/images/%Y-%m-%d'
    collection_class = PhotoCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_desktop_name = storage.resource.desktop.name
        storage.old_mobile_name = storage.resource.mobile.name
        storage.old_admin_preview_name = storage.resource.admin_preview.name

        storage.old_source_path = file.path
        storage.old_desktop_path = storage.resource.desktop.path
        storage.old_mobile_path = storage.resource.mobile.path
        storage.old_admin_preview_path = storage.resource.admin_preview.path

        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_name(self, storage):
        super().test_file_name(storage)
        assert storage.old_admin_preview_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.admin_preview.jpg'),
            storage.old_source_name
        )

    def test_file_not_exists(self, storage):
        super().test_file_not_exists(storage)
        assert os.path.exists(storage.old_admin_preview_path) is False


class TestImageItemEmpty(TestImageEmpty):
    recource_class = ImageItem
    collection_class = PhotoCollection

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
        storage.collection = PhotoCollection.objects.create()

        storage.resource = ImageItem()
        storage.resource.attach_to(storage.collection)
        with open(NASA_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
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
