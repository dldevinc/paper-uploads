import os
from contextlib import contextmanager

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from examples.collections.custom_models.models import CustomCollection
from examples.collections.custom_models.models import ImageItem as CustomImageItem
from examples.collections.standard.models import (
    FilesOnlyCollection,
    ImagesOnlyCollection,
    MixedCollection,
    Page,
)

from paper_uploads import exceptions, helpers
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
    TestVersatileImageEmpty,
    TestVersatileImageRename,
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

    def test_declared_item_types(self):
        """
        Проверка классов элементов коллекции, объявленных в самих классах.
        Унаследованные классы не учитываются.
        """
        collection_types = _get_item_types(Collection)
        assert collection_types == {}

        image_collection_types = _get_item_types(ImageCollection)
        assert list(image_collection_types.keys()) == ["image"]

        file_collection_types = _get_item_types(FilesOnlyCollection)
        assert list(file_collection_types.keys()) == ["file"]

        photo_collection_types = _get_item_types(ImagesOnlyCollection)
        assert list(photo_collection_types.keys()) == []

        custom_collection_types = _get_item_types(CustomCollection)
        assert list(custom_collection_types.keys()) == ["image"]

        mixed_collection_types = _get_item_types(MixedCollection)
        assert list(mixed_collection_types.keys()) == ["svg", "image", "file"]

    def test_item_types(self):
        assert Collection.item_types == {}
        assert list(ImageCollection.item_types.keys()) == ["image"]
        assert list(ImagesOnlyCollection.item_types.keys()) == ["image"]
        assert list(FilesOnlyCollection.item_types.keys()) == ["file"]
        assert list(CustomCollection.item_types.keys()) == ["image"]
        assert list(MixedCollection.item_types.keys()) == ["svg", "image", "file"]


class TestCollection:
    @staticmethod
    def init_class(storage):
        # collection #1 (files only)
        storage.file_collection = FilesOnlyCollection.objects.create()

        # collection #2 (images only)
        storage.image_collection = ImagesOnlyCollection.objects.create()

        # collection #3 (all types allowed)
        storage.mixed_collection = MixedCollection.objects.create()

        file_item = FileItem()
        file_item.attach_to(storage.file_collection)
        file_item.attach(DOCUMENT_FILEPATH, name="file_c1.pdf")
        file_item.save()

        image_item = ImageItem()
        image_item.attach_to(storage.image_collection)
        image_item.attach(NATURE_FILEPATH, name="image_c2.jpg")
        image_item.save()

        file_item = FileItem()
        file_item.attach_to(storage.mixed_collection)
        file_item.attach(CALLIPHORA_FILEPATH, name="file_c3.jpg")
        file_item.save()

        image_item = ImageItem()
        image_item.attach_to(storage.mixed_collection)
        image_item.attach(NASA_FILEPATH, name="image_c3.jpg")
        image_item.save()

        svg_item = SVGItem()
        svg_item.attach_to(storage.mixed_collection)
        svg_item.attach(MEDITATION_FILEPATH, name="svg_c3.svg")
        svg_item.save()

        yield

        for collection in {
            storage.file_collection,
            storage.image_collection,
            storage.mixed_collection
        }:
            for c_item in collection.get_items().all():
                c_item.delete_file()
            collection.delete()

    def test_created_at(self, storage):
        assert utils.is_equal_dates(storage.file_collection.created_at, storage.now)

    def test_item_count(self, storage):
        assert storage.file_collection.get_items().count() == 1
        assert storage.image_collection.get_items().count() == 1
        assert storage.mixed_collection.get_items().count() == 3

    def test_order_values(self, storage):
        order_values = storage.mixed_collection.get_items().values_list("order", flat=True)
        assert sorted(order_values) == [0, 1, 2]

    def test_get_next_order_value(self, storage):
        image_item = storage.mixed_collection.get_items("image").first()
        assert image_item.get_next_order_value() == 3

    def test_get_items(self, storage):
        assert storage.file_collection.get_items("file").count() == 1
        assert storage.mixed_collection.get_items("file").count() == 1

        assert storage.image_collection.get_items("image").count() == 1
        assert storage.mixed_collection.get_items("image").count() == 1

        assert storage.mixed_collection.get_items("svg").count() == 1

    def test_get_items_on_concrete_model(self, storage):
        collection = Collection.objects.get(pk=storage.mixed_collection.pk)
        assert collection.get_items().count() == 3

    def test_iter(self, storage):
        iterator = iter(storage.mixed_collection)

        assert isinstance(next(iterator), FileItem)
        assert isinstance(next(iterator), ImageItem)
        assert isinstance(next(iterator), SVGItem)

        with pytest.raises(StopIteration):
            next(iterator)

    def test_get_unsupported_items(self, storage):
        with pytest.raises(exceptions.InvalidItemType):
            storage.file_collection.get_items("image")

        with pytest.raises(exceptions.InvalidItemType):
            storage.image_collection.get_items("file")

        with pytest.raises(exceptions.InvalidItemType):
            storage.mixed_collection.get_items("nothing")

    def test_collection_id(self, storage):
        for item1 in storage.file_collection.get_items():
            assert item1.collection_id == 1

        for item2 in storage.image_collection.get_items():
            assert item2.collection_id == 2

        for item3 in storage.mixed_collection.get_items():
            assert item3.collection_id == 3

    def test_manager(self, storage):
        assert Collection.objects.count() == 3
        assert FilesOnlyCollection.objects.count() == 1
        assert ImagesOnlyCollection.objects.count() == 1
        assert MixedCollection.objects.count() == 1

    def test_get_collection_class(self, storage):
        file1, file2 = FileItem.objects.order_by("id")
        assert file1.get_collection_class() is FilesOnlyCollection
        assert file2.get_collection_class() is MixedCollection

    def test_get_item_type_field(self, storage):
        image_item1 = storage.image_collection.get_items("image").first()
        assert image_item1.get_item_type_field() is ImagesOnlyCollection.item_types["image"]

        image_item2 = storage.mixed_collection.get_items("image").first()
        assert image_item2.get_item_type_field() is MixedCollection.item_types["image"]

        svg_item = storage.mixed_collection.get_items("svg").first()
        assert svg_item.get_item_type_field() is MixedCollection.item_types["svg"]

    def test_attach_to_file_collection(self, storage):
        file_item = FileItem()
        file_item.attach_to(storage.file_collection)

        assert file_item.collection_id == storage.file_collection.pk
        assert file_item.collection_content_type == ContentType.objects.get_for_model(
            FilesOnlyCollection, for_concrete_model=False)
        assert file_item.type == "file"

    def test_attach_to_mixed_collection(self, storage):
        file_item = FileItem()
        file_item.attach_to(storage.mixed_collection)

        assert file_item.collection_id == storage.mixed_collection.pk
        assert file_item.collection_content_type == ContentType.objects.get_for_model(
            MixedCollection, for_concrete_model=False)
        assert file_item.type == "file"

    def test_get_preview_url(self):
        file_item = FileItem(extension="pdf")
        assert file_item.get_preview_url() == "/static/paper_uploads/dist/assets/pdf.svg"

        file_item = FileItem(extension="mp4")
        assert file_item.get_preview_url() == "/static/paper_uploads/dist/assets/mp4.svg"

        file_item = FileItem(extension="docx")
        assert file_item.get_preview_url() == "/static/paper_uploads/dist/assets/doc.svg"

        file_item = FileItem(extension="ogg")
        assert file_item.get_preview_url() == "/static/paper_uploads/dist/assets/audio.svg"

        file_item = FileItem(extension="py")
        assert file_item.get_preview_url() == "/static/paper_uploads/dist/assets/unknown.svg"

    def test_set_owner_field(self, storage):
        storage.file_collection.set_owner_field(Page, "file_collection")
        assert storage.file_collection.owner_app_label == "standard_collections"
        assert storage.file_collection.owner_model_name == "page"
        assert storage.file_collection.owner_fieldname == "file_collection"
        assert storage.file_collection.get_owner_model() is Page
        assert storage.file_collection.get_owner_field() is Page._meta.get_field("file_collection")

    def test_get_item_model(self, storage):
        assert storage.mixed_collection.get_item_model("svg") is SVGItem
        assert storage.mixed_collection.get_item_model("image") is ImageItem
        assert storage.mixed_collection.get_item_model("file") is FileItem
        with pytest.raises(exceptions.InvalidItemType):
            storage.mixed_collection.get_item_model("video")


@pytest.mark.django_db
def test_get_last_modified():
    collection = CustomCollection.objects.create()
    date1 = collection.get_last_modified()

    # add item
    image_item = CustomImageItem()
    image_item.attach_to(collection)
    image_item.attach(NASA_FILEPATH, name="image_{}.jpg".format(get_random_string(6)))
    image_item.save()

    date2 = collection.get_last_modified()
    assert date2 > date1

    # modify item
    image_item.title = "Nasa"
    image_item.save()

    date3 = collection.get_last_modified()
    assert date3 > date2

    # add more items
    image_item = CustomImageItem()
    image_item.attach_to(collection)
    image_item.attach(CALLIPHORA_FILEPATH, name="image_{}.jpg".format(get_random_string(6)))
    image_item.save()

    date4 = collection.get_last_modified()
    assert date4 > date3

    # delete items
    collection.get_items().delete()

    collection.refresh_from_db()
    date5 = collection.get_last_modified()
    assert date5 > date4

    collection.delete()


@pytest.mark.django_db
class TestDeleteCustomImageCollection:
    def _create_collection(self):
        collection = CustomCollection.objects.create()

        image_item = CustomImageItem()
        image_item.attach_to(collection)
        image_item.attach(NASA_FILEPATH, name="image_del.jpg")
        image_item.save()

        return collection

    def test_explicit_deletion(self):
        collection = self._create_collection()
        item = collection.get_items().first()  # type: CustomImageItem
        item_files = [item.get_file(), *(pair[1] for pair in item.variation_files())]

        collection.delete()

        for vfile in item_files:
            vfile.delete()

    def test_sql_deletion(self):
        collection = self._create_collection()
        item = collection.get_items().first()  # type: CustomImageItem
        item_files = [item.get_file(), *(pair[1] for pair in item.variation_files())]

        CustomCollection.objects.filter(pk=collection.pk).delete()

        for vfile in item_files:
            vfile.delete()


@pytest.mark.django_db
class TestAttachWrongItemClassToCollection:
    def test_attach(self):
        collection = ImagesOnlyCollection.objects.create()
        resource = FileItem()

        with pytest.raises(exceptions.UnsupportedCollectionItemError):
            resource.attach_to(collection)

        collection.delete()


class CollectionItemMixin:
    collection_class = None

    def test_item_type(self, storage):
        raise NotImplementedError

    def test_collection_content_type(self, storage):
        assert storage.resource.collection_content_type == ContentType.objects.get_for_model(
            self.collection_class,
            for_concrete_model=False
        )

    def test_concrete_collection_content_type(self, storage):
        assert storage.resource.concrete_collection_content_type == ContentType.objects.get_for_model(
            self.collection_class,
            for_concrete_model=True
        )

    def test_get_collection_class(self, storage):
        assert storage.resource.get_collection_class() is self.collection_class

    def test_collection_id(self, storage):
        assert storage.resource.collection_id == storage.collection.pk

    def test_get_next_order_value(self, storage):
        assert storage.resource.get_next_order_value() == 1

    def test_order(self, storage):
        assert storage.resource.order == 0

    def test_get_caption(self, storage):
        assert storage.resource.get_caption() == "{}.{}".format(
            self.resource_basename,  # noqa: F821
            self.resource_extension  # noqa: F821
        )

    def test_file_not_exists(self):
        collection = self.collection_class.objects.create()
        resource = self.resource_class()
        resource.attach_to(collection)
        resource.resource_name = "non-existent-file"
        resource.extension = self.resource_extension
        assert resource.file_exists() is False
        collection.delete()

    def test_accept(self, storage):
        raise NotImplementedError


class CollectionItemTestBase(CollectionItemMixin, TestFileFieldResource):
    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()


class CollectionItemAttachTestBase(TestFileFieldResourceAttach):
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


class CollectionItemDeleteTestBase(TestFileFieldResourceDelete):
    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(
            cls.resource_attachment,
            name="file_{}.jpg".format(get_random_string(6))
        )
        storage.resource.save()

        storage.old_resource_name = storage.resource.name

        storage.resource.delete_file()
        yield

        storage.resource.delete()
        storage.collection.delete()


# ======================================================================================


class TestFileItem(CollectionItemTestBase):
    collection_class = FilesOnlyCollection
    resource_class = FileItem
    resource_attachment = NATURE_FILEPATH
    resource_basename = "Nature Tree"
    resource_extension = "Jpeg"
    resource_name = "collections/files/%Y/%m/%d/Nature_Tree{suffix}.Jpeg"
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    resource_folder = "collections/files/%Y/%m/%d"
    resource_field_name = "file"

    def test_item_type(self, storage):
        assert storage.resource.type == "file"

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "collectionId": 1,
                "itemType": "file",  # TODO: deprecated
                "type": "file",
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "url": storage.resource.url,
                "order": 0,
                "preview": render_to_string(
                    "paper_uploads/items/preview/file.html",
                    storage.resource.get_preview_context()
                ),
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id", "collectionId"}
        )

    def test_accept(self, storage):
        with open(DOCUMENT_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(NATURE_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(MEDITATION_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True


@pytest.mark.django_db
class TestFileItemAttach(CollectionItemAttachTestBase):
    collection_class = MixedCollection
    resource_class = FileItem
    resource_attachment = DOCUMENT_FILEPATH
    resource_basename = "document"
    resource_extension = "pdf"
    resource_size = 3028
    resource_checksum = "93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e"


class TestFileItemRename(TestFileFieldResourceRename):
    collection_class = FilesOnlyCollection
    resource_class = FileItem
    resource_attachment = NATURE_FILEPATH
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    old_name = "old_name_{}.txt".format(get_random_string(6))
    new_name = "new_name_{}.log".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name
        storage.old_resource_path = storage.resource.path

        storage.resource.rename(cls.new_name)
        yield

        os.unlink(storage.old_resource_path)
        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()


class TestFileItemDelete(CollectionItemDeleteTestBase):
    collection_class = FilesOnlyCollection
    resource_class = FileItem
    resource_attachment = EXCEL_FILEPATH


class TestFileItemEmpty(TestFileFieldResourceEmpty):
    recource_class = FileItem


class TestSVGItem(CollectionItemTestBase):
    collection_class = MixedCollection
    resource_class = SVGItem
    resource_attachment = MEDITATION_FILEPATH
    resource_basename = "Meditation"
    resource_extension = "svg"
    resource_name = "collections/files/%Y/%m/%d/Meditation{suffix}.svg"
    resource_size = 47193
    resource_checksum = "7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d"
    resource_folder = "collections/files/%Y/%m/%d"
    resource_field_name = "file"

    def test_name(self, storage):
        assert utils.match_path(
            storage.resource.name,
            "{}/Meditation{{suffix}}.svg".format(self.resource_folder),
        )

    def test_item_type(self, storage):
        assert storage.resource.type == "svg"

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "collectionId": 1,
                "itemType": "svg",  # TODO: deprecated
                "type": "svg",
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "width": "626",
                "height": "660.0532",
                "title": "",
                "description": "",
                "url": storage.resource.url,
                "order": 0,
                "preview": render_to_string(
                    "paper_uploads/items/preview/svg.html",
                    storage.resource.get_preview_context()
                ),
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id", "collectionId"}
        )

    def test_path(self, storage):
        assert utils.match_path(
            storage.resource.path,
            "/media/{}/Meditation{{suffix}}.svg".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert utils.match_path(
            storage.resource.url,
            "/media/{}/Meditation{{suffix}}.svg".format(self.resource_folder),
        )

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(5) == b'<?xml'

    def test_accept(self, storage):
        with open(DOCUMENT_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(MEDITATION_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False


@pytest.mark.django_db
class TestSVGItemAttach(CollectionItemAttachTestBase):
    collection_class = MixedCollection
    resource_class = SVGItem
    resource_attachment = MEDITATION_FILEPATH
    resource_basename = "Meditation"
    resource_extension = "svg"
    resource_size = 47193
    resource_checksum = "7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d"

    def test_unsupported_file(self):
        resource = self.resource_class()
        with pytest.raises(exceptions.UnsupportedResource):
            resource.attach(AUDIO_FILEPATH)


class TestSVGItemRename(TestFileFieldResourceRename):
    collection_class = MixedCollection
    resource_class = SVGItem
    resource_attachment = MEDITATION_FILEPATH
    resource_size = 47193
    resource_checksum = "7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d"
    old_name = "old_name_{}.svg".format(get_random_string(6))
    new_name = "new_name_{}.svg".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name
        storage.old_resource_path = storage.resource.path

        storage.resource.rename(cls.new_name)
        yield

        os.unlink(storage.old_resource_path)
        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()


class TestSVGItemDelete(CollectionItemDeleteTestBase):
    collection_class = MixedCollection
    resource_class = SVGItem
    resource_attachment = MEDITATION_FILEPATH


class TestSVGItemEmpty(TestFileFieldResourceEmpty):
    recource_class = SVGItem


class TestImageItem(CollectionItemTestBase):
    collection_class = ImagesOnlyCollection
    resource_class = ImageItem
    resource_attachment = NATURE_FILEPATH
    resource_basename = "Nature Tree"
    resource_extension = "jpg"
    resource_name = "collections/images/%Y/%m/%d/Nature_Tree{suffix}.jpg"
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    resource_folder = "collections/images/%Y/%m/%d"
    resource_field_name = "file"

    def test_name(self, storage):
        assert utils.match_path(
            storage.resource.name,
            "{}/Nature_Tree{{suffix}}.jpg".format(self.resource_folder),
        )

    def test_item_type(self, storage):
        assert storage.resource.type == "image"

    def test_path(self, storage):
        assert utils.match_path(
            storage.resource.path,
            "/media/{}/Nature_Tree{{suffix}}.jpg".format(self.resource_folder),
        )

    def test_url(self, storage):
        assert utils.match_path(
            storage.resource.url,
            "/media/{}/Nature_Tree{{suffix}}.jpg".format(self.resource_folder),
        )

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(5) == b'\xff\xd8\xff\xe0\x00'

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "collectionId": 1,
                "itemType": "image",  # TODO: deprecated
                "type": "image",
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "width": 1534,
                "height": 2301,
                "cropregion": "",
                "title": "",
                "description": "",
                "order": 0,
                "preview": render_to_string(
                    "paper_uploads/items/preview/image.html",
                    storage.resource.get_preview_context()
                ),
                "url": storage.resource.get_file_url(),
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id", "collectionId"}
        )

    def test_get_variations(self, storage):
        variations = storage.resource.get_variations()

        assert "desktop" in variations
        assert "admin_preview" in variations
        assert "admin_preview_webp" in variations
        assert "admin_preview_webp_2x" in variations

        assert variations["desktop"].size == (800, 0)
        assert variations["mobile"].size == (0, 600)

        # admin variation overriden
        assert variations["admin_preview"].size == (180, 135)
        assert variations["admin_preview"].format == "JPEG"

        # ensure that setting has not changed
        assert ImageItem.PREVIEW_VARIATIONS["admin_preview"]["size"] == (180, 135)
        assert IMAGE_ITEM_VARIATIONS["admin_preview"]["size"] == (180, 135)

    def test_get_variations_on_empty_resource(self):
        resource = self.resource_class()
        variations = resource.get_variations()
        assert variations == {}

    @pytest.mark.django_db
    def test_get_variations_on_minimal_resource(self):
        resource = self.resource_class(
            collection_content_type_id=ContentType.objects.get_for_model(
                self.collection_class,
                for_concrete_model=False
            ).pk,
            concrete_collection_content_type_id=ContentType.objects.get_for_model(
                self.collection_class
            ).pk,
            type="image"
        )
        variations = resource.get_variations()
        assert len(variations) == 6

    def test_width(self, storage):
        assert storage.resource.width == 1534

    def test_height(self, storage):
        assert storage.resource.height == 2301

    def test_accept(self, storage):
        with open(DOCUMENT_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        # SVG passes image test
        with open(MEDITATION_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, "rb") as fp:
            assert storage.resource.accept(File(fp)) is False


@pytest.mark.django_db
class TestImageItemAttach(CollectionItemAttachTestBase):
    collection_class = ImagesOnlyCollection
    resource_class = ImageItem
    resource_attachment = NASA_FILEPATH
    resource_basename = "milky-way-nasa"
    resource_extension = "jpg"
    resource_size = 9711423
    resource_checksum = "485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0"

    def test_django_file(self):
        with self.get_resource() as resource:
            overriden_name = "milky-way-nasa_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_django_file_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/milky-way-nasa_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name=overriden_name)
                resource.attach(file)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "photos/overwritten_{}.gif".format(get_random_string(6))
            resource.attach(self.resource_attachment, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_django_name(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="not_used.png")
                resource.attach(file, name=overriden_name)

            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_override_django_name_with_relative_path(self):
        with self.get_resource() as resource:
            overriden_name = "overwritten_{}.gif".format(get_random_string(6))
            with open(self.resource_attachment, "rb") as fp:
                file = File(fp, name="photos/not_used.png")
                resource.attach(file, name=overriden_name)

            assert "/photos/" not in resource.name
            assert resource.resource_name == helpers.get_filename(overriden_name)
            assert resource.extension == self.resource_extension

    def test_unsupported_file(self):
        resource = self.resource_class()
        with pytest.raises(exceptions.UnsupportedResource):
            resource.attach(AUDIO_FILEPATH)


class TestImageItemRename(TestVersatileImageRename):
    collection_class = ImagesOnlyCollection
    resource_class = ImageItem
    resource_attachment = NATURE_FILEPATH
    resource_size = 672759
    resource_checksum = "e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1"
    old_name = "old_name_{}.tiff".format(get_random_string(6))
    new_name = "new_name_{}.tif".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name
        storage.old_resource_path = storage.resource.path
        storage.old_resource_desktop_path = storage.resource.desktop.path
        storage.old_resource_mobile_path = storage.resource.mobile.path
        storage.old_resource_mobile_path = storage.resource.mobile.path
        storage.old_resource_admin_preview_path = storage.resource.admin_preview.path
        storage.old_resource_admin_preview_2x_path = storage.resource.admin_preview_2x.path
        storage.old_resource_admin_preview_webp_path = storage.resource.admin_preview_webp.path
        storage.old_resource_admin_preview_webp_2x_path = storage.resource.admin_preview_webp_2x.path

        storage.resource.rename(cls.new_name)
        yield

        os.unlink(storage.old_resource_path)
        os.unlink(storage.old_resource_desktop_path)
        os.unlink(storage.old_resource_mobile_path)
        os.unlink(storage.old_resource_admin_preview_path)
        os.unlink(storage.old_resource_admin_preview_2x_path)
        os.unlink(storage.old_resource_admin_preview_webp_path)
        os.unlink(storage.old_resource_admin_preview_webp_2x_path)
        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()


class TestImageItemDelete(CollectionItemDeleteTestBase):
    collection_class = ImagesOnlyCollection
    resource_class = ImageItem
    resource_attachment = NATURE_FILEPATH


class TestImageItemEmpty(TestVersatileImageEmpty):
    recource_class = ImageItem


class TestInvalidCollectionContentType:
    @classmethod
    def init_class(cls, storage):
        storage.content_type = ContentType.objects.create(
            app_label="standard_collections",
            model="deletedmodel"
        )

        storage.collection = Collection.objects.create(
            collection_content_type=storage.content_type,
            concrete_collection_content_type=ContentType.objects.get_for_model(Collection),
            owner_app_label="standard_collections",
            owner_model_name="page",
            owner_fieldname="temp_collection"
        )

        storage.file_item = FileItem.objects.create(
            pk=1,
            collection_content_type_id=storage.content_type.pk,
            concrete_collection_content_type_id=storage.collection.concrete_collection_content_type.pk,
            collection_id=storage.collection.pk,
            order=1
        )
        with open(DOCUMENT_FILEPATH, "rb") as fp:
            storage.file_item.file.save("invalid_ct.pdf", fp)

        storage.image_item = FileItem.objects.create(
            pk=2,
            collection_content_type_id=storage.content_type.pk,
            concrete_collection_content_type_id=storage.collection.concrete_collection_content_type.pk,
            collection_id=storage.collection.pk,
            order=2
        )
        with open(NATURE_FILEPATH, "rb") as fp:
            storage.image_item.file.save("invalid_ct.jpg", fp)

        yield

        storage.file_item.delete_file()
        storage.file_item.delete()

        storage.image_item.delete_file()
        storage.image_item.delete()

        storage.collection.delete()

    def test_collection_class(self, storage):
        ct = ContentType.objects.get_for_id(storage.collection.collection_content_type_id)
        assert ct.model_class() is None

    def test_get_owner_model(self, storage):
        assert storage.collection.get_owner_model() is Page

    def test_get_items(self, storage):
        assert storage.collection.get_items().count() == 2

    def test_get_collection_class(self, storage):
        with pytest.raises(exceptions.CollectionModelNotFoundError):
            storage.file_item.get_collection_class()

    def test_get_item_type_field(self, storage):
        with pytest.raises(exceptions.CollectionModelNotFoundError):
            assert storage.file_item.get_item_type_field() is None

    def test_attach_to(self, storage):
        item = FileItem()
        with pytest.raises(exceptions.UnsupportedCollectionItemError):
            item.attach_to(storage.collection)
