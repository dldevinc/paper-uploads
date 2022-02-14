import json

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.test import RequestFactory
from examples.fields.proxy_models.models import Page, UploadedFileProxy

from paper_uploads.exceptions import InvalidContentType, InvalidObjectId
from paper_uploads.forms.dialogs.file import ChangeUploadedFileDialog
from paper_uploads.views.file import ChangeFileView, DeleteFileView, UploadFileView


class TestUploadFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(UploadedFileProxy, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = UploadFileView()
        yield

    def test_get_file_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        file_model = storage.view.get_file_model()
        assert file_model is UploadedFileProxy

    def test_get_instance(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "proxy_models_fields",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "file"
        })
        request.user = storage.user
        storage.view.setup(request)

        instance = storage.view.get_instance()
        assert isinstance(instance, UploadedFileProxy)
        assert instance.pk is None
        assert instance.get_owner_field() is Page._meta.get_field("file")

    def test_invalid_content_type(self, storage):
        wrong_content_type = ContentType.objects.get_for_model(User, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperContentType": wrong_content_type.pk,
            "paperOwnerAppLabel": "proxy_models_fields",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "file"
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
            "paperOwnerFieldName": "filter_ext"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ValidationError, match="has an invalid extension"):
            storage.view.handle(ContentFile(b'', name="dummy.exe"))

    def test_success(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "proxy_models_fields",
            "paperOwnerModelName": "page",
            "paperOwnerFieldName": "file"
        })
        request.user = storage.user
        storage.view.setup(request)

        response = storage.view.handle(ContentFile(b'Hello, dude', name="dummy.txt"))
        assert isinstance(response, JsonResponse)
        assert json.loads(response.content)["name"] == "dummy"

        item_id = json.loads(response.content)["id"]
        item = UploadedFileProxy.objects.get(pk=item_id)
        item.delete_file()
        item.delete()


class TestDeleteFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(UploadedFileProxy, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = DeleteFileView()
        yield

    def test_get_file_model(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        file_model = storage.view.get_file_model()
        assert file_model is UploadedFileProxy

    def test_invalid_content_type(self, storage):
        wrong_content_type = ContentType.objects.get_for_model(User, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperContentType": wrong_content_type.pk,
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
        file = UploadedFileProxy(
            pk=5486
        )
        file.set_owner_field(Page, "file")
        file.save()

        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": file.pk
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
        storage.content_type = ContentType.objects.get_for_model(UploadedFileProxy, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.object = UploadedFileProxy(
            pk=5487
        )
        storage.object.set_owner_field(Page, "file")
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
        assert form_class is ChangeUploadedFileDialog

    def test_get_file_model(self, storage):
        request = RequestFactory().get("/", data={
            "paperContentType": storage.content_type.pk,
        })
        request.user = storage.user
        storage.view.setup(request)

        file_model = storage.view.get_file_model()
        assert file_model is UploadedFileProxy

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
