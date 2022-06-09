import json

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.test import RequestFactory
from examples.fields.proxy_models.models import Page, UploadedImageProxy

from paper_uploads.exceptions import InvalidContentType, InvalidObjectId
from paper_uploads.forms.dialogs.image import ChangeUploadedImageDialog
from paper_uploads.views.image import ChangeFileView, DeleteFileView, UploadFileView

from ..dummy import *


class TestUploadFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(UploadedImageProxy, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = UploadFileView()
        yield

    def test_get_file_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        file_model = storage.view.get_file_model()
        assert file_model is UploadedImageProxy

    def test_get_instance(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "proxy_models_fields",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "image"
        })
        request.user = storage.user
        storage.view.setup(request)

        instance = storage.view.get_instance()
        assert isinstance(instance, UploadedImageProxy)
        assert instance.pk is None
        assert instance.get_owner_field() is Page._meta.get_field("image")

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperContentType": content_type.pk,
            "paperOwnerAppLabel": "proxy_models_fields",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "image"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_instance()

    def test_validation_errors(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "validators_fields",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "filter_image_ext"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ValidationError, match="has an invalid extension"):
            with open(NASA_FILEPATH, "rb") as fp:
                storage.view.handle(fp)

    def test_success(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "proxy_models_fields",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "image"
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

        item_id = json.loads(response.content)["id"]
        item = UploadedImageProxy.objects.get(pk=item_id)
        item.delete_file()
        item.delete()


class TestDeleteFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(UploadedImageProxy, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.view = DeleteFileView()
        yield

    def test_get_file_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        file_model = storage.view.get_file_model()
        assert file_model is UploadedImageProxy

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperContentType": content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_file_model()

    def test_get_file_id(self, storage):
        request = RequestFactory().post("/", data={
            "pk": "53",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_file_id() == "53"

    def test_invalid_id(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": "five"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidObjectId):
            storage.view.get_instance()

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            storage.view.get_instance()

    def test_success(self, storage):
        file = UploadedImageProxy(
            pk=5472
        )
        file.set_owner_field(Page, "image")
        file.save()

        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": 5472
        })
        request.user = storage.user
        storage.view.setup(request)

        response = storage.view.handle()
        assert isinstance(response, JsonResponse)
        assert response.status_code == 200
        assert json.loads(response.content) == {}

        file.delete_file()
        file.delete()


class TestChangeFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(UploadedImageProxy, for_concrete_model=False)
        storage.user = User.objects.get(username="jon")
        storage.object = UploadedImageProxy(
            pk=5479
        )
        storage.object.set_owner_field(Page, "image")
        storage.object.save()

        storage.view = ChangeFileView()

        yield

    def test_form_class(self, storage):
        request = RequestFactory().get("/", data={
            "paperContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        form_class = storage.view.get_form_class()
        assert form_class is ChangeUploadedImageDialog

    def test_get_file_model(self, storage):
        request = RequestFactory().get("/", data={
            "paperContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        file_model = storage.view.get_file_model()
        assert file_model is UploadedImageProxy

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(Page, for_concrete_model=False)

        request = RequestFactory().get("/", data={
            "paperContentType": content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_file_model()

    def test_get_file_id(self, storage):
        request = RequestFactory().get("/", data={
            "pk": "53",
        })
        request.user = storage.user
        storage.view.setup(request)

        assert storage.view.get_file_id() == "53"

    def test_invalid_id(self, storage):
        request = RequestFactory().get("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": "five"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidObjectId):
            storage.view.get_instance()

    def test_object_not_found(self, storage):
        request = RequestFactory().get("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": 9999
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ObjectDoesNotExist):
            storage.view.get_instance()
