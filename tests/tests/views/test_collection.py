import json
import os

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse
from django.test import RequestFactory
from examples.collections.custom_models.dialogs import ChangeUploadedCustomImageDialog
from examples.collections.custom_models.models import CustomCollection
from examples.collections.custom_models.models import ImageItem as CustomImageItem
from examples.collections.custom_models.models import Page as CustomPage
from examples.collections.standard.models import (
    FilesOnlyCollection,
    ImagesOnlyCollection,
    MixedCollection,
    Page,
)

from paper_uploads.exceptions import InvalidContentType, InvalidItemType, InvalidObjectId
from paper_uploads.models import ImageItem
from paper_uploads.views.collection import (
    ChangeFileView,
    CreateCollectionView,
    DeleteCollectionView,
    DeleteFileView,
    SortItemsView,
    UploadFileView,
)

from ..dummy import *


class TestCreateCollectionView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(FilesOnlyCollection, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = CreateCollectionView()
        yield

    def test_get_instance(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "standard_collections",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "file_collection"
        })
        request.user = storage.user
        storage.view.setup(request)

        instance = storage.view.get_instance()
        assert isinstance(instance, FilesOnlyCollection)
        assert instance.pk is None
        assert instance.get_owner_field() is Page._meta.get_field("file_collection")

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": content_type.pk,
            "paperOwnerAppLabel": "standard_collections",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "file_collection"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_instance()

    def test_success(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "standard_collections",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "file_collection"
        })
        request.user = storage.user
        storage.view.setup(request)

        response = storage.view.handle()
        assert isinstance(response, JsonResponse)
        assert type(json.loads(response.content)["collection_id"]) is int


class TestDeleteCollectionView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(FilesOnlyCollection, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = DeleteCollectionView()
        yield

    def test_get_collection_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        collection_cls = storage.view.get_collection_model()
        assert collection_cls is FilesOnlyCollection

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_collection_model()

    def test_get_collection_id(self, storage):
        request = RequestFactory().post("/", data={
            "collectionId": "53",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_collection_id() == "53"

    def test_invalid_id(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": "five"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidObjectId):
            storage.view.get_instance()

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            storage.view.get_instance()

    def test_success(self, storage):
        collection = FilesOnlyCollection(
            pk=5489
        )
        collection.set_owner_field(Page, "file_collection")
        collection.save()

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": collection.pk
        })
        request.user = storage.user
        storage.view.setup(request)

        response = storage.view.handle()
        assert isinstance(response, JsonResponse)
        assert response.status_code == 200
        assert json.loads(response.content) == {}

        collection.delete()


class TestUploadFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(FilesOnlyCollection, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = UploadFileView()
        yield

    def test_get_collection_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        collection_cls = storage.view.get_collection_model()
        assert collection_cls is FilesOnlyCollection

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_collection_model()

    def test_get_collection_id(self, storage):
        request = RequestFactory().post("/", data={
            "collectionId": "78",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_collection_id() == "78"

    def test_invalid_id(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": "five"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidObjectId):
            with open(NASA_FILEPATH, "rb") as fp:
                storage.view.handle(fp)

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            with open(NASA_FILEPATH, "rb") as fp:
                storage.view.handle(fp)

    def test_unsupported_item_type(self, storage):
        collection = ImagesOnlyCollection(
            pk=9562
        )
        collection.set_owner_field(Page, "image_collection")
        collection.save()

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": ContentType.objects.get_for_model(ImagesOnlyCollection, for_concrete_model=False).pk,
            "collectionId": "9562",
        })
        request.user = storage.user
        storage.view.setup(request)

        with open(AUDIO_FILEPATH, "rb") as fp:
            uploaded_file = UploadedFile(
                file=fp,
                name=os.path.basename(fp.name),
                size=os.path.getsize(fp.name)
            )
            response = storage.view.handle(uploaded_file)

        assert isinstance(response, JsonResponse)

        response_data = json.loads(response.content)
        assert "errors" in response_data
        assert "Unsupported file" in response_data["errors"][0]

        collection.delete()

    def test_success(self, storage):
        collection = FilesOnlyCollection(
            pk=9563
        )
        collection.set_owner_field(Page, "file_collection")
        collection.save()

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": "9563",
        })
        request.user = storage.user
        storage.view.setup(request)

        response = storage.view.handle(
            ContentFile(
                b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;',
                name="dummy.gif"
            )
        )
        assert isinstance(response, JsonResponse)
        assert json.loads(response.content)["name"] == "dummy"
        assert collection.get_items().count() == 1

        item_id = json.loads(response.content)["id"]
        item = collection.get_items().get(pk=item_id)
        item.delete_file()

        collection.delete()

    def test_get_accepted_item_types(self, storage):
        with open(DOCUMENT_FILEPATH, "rb") as fp:
            file = UploadedFile(
                file=fp,
                name=os.path.basename(fp.name),
                size=os.path.getsize(fp.name)
            )
            gen = storage.view.get_accepted_item_types(FilesOnlyCollection, file)
            item_type, _ = next(gen)
            assert item_type == "file"

        with open(NATURE_FILEPATH, "rb") as fp:
            file = UploadedFile(
                file=fp,
                name=os.path.basename(fp.name),
                size=os.path.getsize(fp.name)
            )
            gen = storage.view.get_accepted_item_types(ImagesOnlyCollection, file)
            item_type, _ = next(gen)
            assert item_type == "image"

        with open(MEDITATION_FILEPATH, "rb") as fp:
            file = UploadedFile(
                file=fp,
                name=os.path.basename(fp.name),
                size=os.path.getsize(fp.name)
            )
            gen = storage.view.get_accepted_item_types(MixedCollection, file)
            item_type, _ = next(gen)
            assert item_type == "svg"

    def test_no_accepted_item_types(self, storage):
        with open(AUDIO_FILEPATH, "rb") as fp:
            file = UploadedFile(
                file=fp,
                name=os.path.basename(fp.name),
                size=os.path.getsize(fp.name)
            )
            gen = storage.view.get_accepted_item_types(ImagesOnlyCollection, file)
            with pytest.raises(StopIteration):
                item_type, _ = next(gen)

    def test_image_accepts_svg(self, storage):
        with open(MEDITATION_FILEPATH, "rb") as fp:
            file = UploadedFile(
                file=fp,
                name=os.path.basename(fp.name),
                size=os.path.getsize(fp.name)
            )
            gen = storage.view.get_accepted_item_types(ImagesOnlyCollection, file)
            item_type, _ = next(gen)
            assert item_type == "image"


class TestDeleteFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomCollection, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = DeleteFileView()

        # collection
        storage.collection = CustomCollection(
            pk=9564
        )
        storage.collection.set_owner_field(CustomPage, "collection")
        storage.collection.save()

        # item
        storage.item = CustomImageItem()
        storage.item.attach_to(storage.collection)
        storage.item.attach(NASA_FILEPATH)
        storage.item.save()

        yield

        storage.item.delete_file()
        storage.collection.delete()

    def test_get_collection_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        collection_cls = storage.view.get_collection_model()
        assert collection_cls is CustomCollection

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_collection_model()

    def test_get_item_type(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_item_type() == "image"

    def test_invalid_item_type(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "file",
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidItemType):
            storage.view.handle()

    def test_get_item_id(self, storage):
        request = RequestFactory().post("/", data={
            "itemId": "78",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_item_id() == "78"

    def test_invalid_id(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image",
            "itemId": "five"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidObjectId):
            storage.view.get_instance()

    def test_success(self, storage):
        assert storage.collection.get_items().count() == 1

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image",
            "itemId": storage.item.pk
        })
        request.user = storage.user
        storage.view.setup(request)

        response = storage.view.handle()
        assert isinstance(response, JsonResponse)
        assert storage.collection.get_items().count() == 0


class TestChangeFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomCollection, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = ChangeFileView()

        # collection
        storage.collection = CustomCollection(
            pk=5965
        )
        storage.collection.set_owner_field(CustomPage, "collection")
        storage.collection.save()

        # item
        storage.item = CustomImageItem()
        storage.item.attach_to(storage.collection)
        storage.item.attach(NASA_FILEPATH)
        storage.item.save()

        yield

        storage.item.delete_file()
        storage.collection.delete()

    def test_form_class(self, storage):
        request = RequestFactory().get("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image"
        })
        request.user = storage.user
        storage.view.setup(request)

        form_class = storage.view.get_form_class()
        assert form_class is ChangeUploadedCustomImageDialog

    def test_get_collection_model(self, storage):
        request = RequestFactory().get("/", data={
            "paperCollectionContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        collection_cls = storage.view.get_collection_model()
        assert collection_cls is CustomCollection

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().get("/", data={
            "paperCollectionContentType": content_type.pk
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_collection_model()

    def test_get_item_type(self, storage):
        request = RequestFactory().get("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_item_type() == "image"

    def test_invalid_item_type(self, storage):
        request = RequestFactory().get("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "file",
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidItemType):
            storage.view.get_instance()

    def test_get_item_id(self, storage):
        request = RequestFactory().get("/", data={
            "itemId": "78",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_item_id() == "78"

    def test_invalid_id(self, storage):
        request = RequestFactory().get("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image",
            "itemId": "five"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidObjectId):
            storage.view.get_instance()

    def test_object_not_found(self, storage):
        request = RequestFactory().get("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image",
            "itemId": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            storage.view.get_instance()


class TestSortItemsView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(ImagesOnlyCollection, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = SortItemsView()

        # collection
        storage.collection = ImagesOnlyCollection(
            pk=9569
        )
        storage.collection.set_owner_field(Page, "file_collection")
        storage.collection.save()

        # item 1
        storage.itemA = ImageItem()
        storage.itemA.attach_to(storage.collection)
        storage.itemA.attach(NASA_FILEPATH)
        storage.itemA.save()

        # item 2
        storage.itemB = ImageItem()
        storage.itemB.attach_to(storage.collection)
        storage.itemB.attach(NATURE_FILEPATH)
        storage.itemB.save()

        # item 3
        storage.itemC = ImageItem()
        storage.itemC.attach_to(storage.collection)
        storage.itemC.attach(CALLIPHORA_FILEPATH)
        storage.itemC.save()

        yield

        storage.itemA.delete_file()
        storage.itemB.delete_file()
        storage.itemC.delete_file()
        storage.collection.delete()

    def test_get_collection_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        collection_cls = storage.view.get_collection_model()
        assert collection_cls is ImagesOnlyCollection

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_collection_model()

    def test_get_collection_id(self, storage):
        request = RequestFactory().post("/", data={
            "collectionId": "53",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_collection_id() == "53"

    def test_invalid_id(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": "five"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidObjectId):
            storage.view.handle()

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            storage.view.handle()

    def test_success(self, storage):
        assert storage.collection.get_items().count() == 3

        orderList = ",".join([
            str(storage.itemB.pk),
            "",     # empty ID
            str(storage.itemC.pk),
            str(storage.itemA.pk),
        ])

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 9569,
            "orderList": orderList
        })
        request.user = storage.user
        storage.view.setup(request)

        response = storage.view.handle()
        response_map = json.loads(response.content)["orderMap"]
        assert response_map == {
            str(storage.itemB.pk): 0,
            str(storage.itemC.pk): 1,
            str(storage.itemA.pk): 2,
        }
