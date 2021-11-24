import json

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.test import RequestFactory

from app.models.custom import CustomGallery, CustomImageItem
from app.models.site import CollectionFieldObject
from paper_uploads.exceptions import InvalidContentType, InvalidItemType, InvalidObjectId
from paper_uploads.views.collection import (
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
        storage.content_type = ContentType.objects.get_for_model(CustomGallery, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = CreateCollectionView()
        yield

    def test_get_instance(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "app",
            "paperOwnerModelName": "collectionfieldobject",
            "paperOwnerFieldName": "custom_collection"
        })
        request.user = storage.user

        storage.view.setup(request)
        instance = storage.view.get_instance()

        assert isinstance(instance, CustomGallery)
        assert instance.pk is None
        assert instance.get_owner_field() is CollectionFieldObject._meta.get_field("custom_collection")

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(CollectionFieldObject, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": content_type.pk,
            "paperOwnerAppLabel": "app",
            "paperOwnerModelName": "collectionfieldobject",
            "paperOwnerFieldName": "custom_collection"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_instance()

    def test_success(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "app",
            "paperOwnerModelName": "collectionfieldobject",
            "paperOwnerFieldName": "custom_collection"
        })
        request.user = storage.user
        storage.view.setup(request)
        response = storage.view.handle(request)

        assert isinstance(response, JsonResponse)
        assert type(json.loads(response.content)["collection_id"]) is int


class TestDeleteCollectionView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomGallery, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = DeleteCollectionView()
        yield

    def test_get_collection_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)
        collection_cls = storage.view.get_collection_model()

        assert collection_cls is CustomGallery

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(CollectionFieldObject, for_concrete_model=False)

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
            storage.view.handle(request)

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            storage.view.handle(request)

    def test_success(self, storage):
        collection = CustomGallery(
            pk=5472
        )
        collection.set_owner_from(CollectionFieldObject._meta.get_field("custom_collection"))
        collection.save()

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 5472
        })
        request.user = storage.user
        storage.view.setup(request)
        response = storage.view.handle(request)

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200
        assert json.loads(response.content) == {}

        collection.delete()


class TestUploadFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomGallery, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = UploadFileView()
        yield

    def test_get_collection_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)
        collection_cls = storage.view.get_collection_model()

        assert collection_cls is CustomGallery

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(CollectionFieldObject, for_concrete_model=False)

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
                storage.view.handle(request, fp)

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            with open(NASA_FILEPATH, "rb") as fp:
                storage.view.handle(request, fp)

    def test_unsupported_item_type(self, storage):
        collection = CustomGallery(
            pk=9562
        )
        collection.set_owner_from(CollectionFieldObject._meta.get_field("custom_collection"))
        collection.save()

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": "9562",
        })
        request.user = storage.user
        storage.view.setup(request)

        with open(AUDIO_FILEPATH, "rb") as fp:
            response = storage.view.handle(request, fp)

        assert isinstance(response, JsonResponse)
        assert "Unsupported file" in json.loads(response.content)["errors"][0]

        collection.delete()

    def test_success(self, storage):
        collection = CustomGallery(
            pk=9563
        )
        collection.set_owner_from(CollectionFieldObject._meta.get_field("custom_collection"))
        collection.save()

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": "9563",
        })
        request.user = storage.user
        storage.view.setup(request)
        response = storage.view.handle(
            request,
            ContentFile(b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;', name="dummy.gif")
        )

        assert isinstance(response, JsonResponse)
        assert json.loads(response.content)["name"] == "dummy"
        assert collection.get_items().count() == 1

        item_id = json.loads(response.content)["id"]
        item = collection.items.get(pk=item_id)
        item.delete_file()

        collection.delete()


class TestDeleteFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomGallery, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = DeleteFileView()

        # collection
        storage.collection = CustomGallery(
            pk=9564
        )
        storage.collection.set_owner_from(CollectionFieldObject._meta.get_field("custom_collection"))
        storage.collection.save()

        # item
        storage.item = CustomImageItem()
        storage.item.attach_to(storage.collection)
        with open(NASA_FILEPATH, "rb") as fp:
            storage.item.attach_file(fp)
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

        assert collection_cls is CustomGallery

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(CollectionFieldObject, for_concrete_model=False)

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
            storage.view.handle(request)

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
            storage.view.handle(request)

    def test_success(self, storage):
        assert storage.collection.get_items().count() == 1

        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "itemType": "image",
            "itemId": storage.item.pk
        })
        request.user = storage.user
        storage.view.setup(request)
        response = storage.view.handle(request)

        assert isinstance(response, JsonResponse)
        assert storage.collection.get_items().count() == 0


class TestSortItemsView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomGallery, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = SortItemsView()

        # collection
        storage.collection = CustomGallery(
            pk=9569
        )
        storage.collection.set_owner_from(CollectionFieldObject._meta.get_field("custom_collection"))
        storage.collection.save()

        # item 1
        storage.itemA = CustomImageItem()
        storage.itemA.attach_to(storage.collection)
        with open(NASA_FILEPATH, "rb") as fp:
            storage.itemA.attach_file(fp)
        storage.itemA.save()

        # item 2
        storage.itemB = CustomImageItem()
        storage.itemB.attach_to(storage.collection)
        with open(NATURE_FILEPATH, "rb") as fp:
            storage.itemB.attach_file(fp)
        storage.itemB.save()

        # item 3
        storage.itemC = CustomImageItem()
        storage.itemC.attach_to(storage.collection)
        with open(CALLIPHORA_FILEPATH, "rb") as fp:
            storage.itemC.attach_file(fp)
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

        assert collection_cls is CustomGallery

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(CollectionFieldObject, for_concrete_model=False)

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
            storage.view.handle(request)

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperCollectionContentType": storage.content_type.pk,
            "collectionId": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            storage.view.handle(request)

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
        response = storage.view.handle(request)
        response_map = json.loads(response.content)["orderMap"]

        assert response_map == {
            str(storage.itemB.pk): 0,
            str(storage.itemC.pk): 1,
            str(storage.itemA.pk): 2,
        }
