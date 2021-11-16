import json

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.test import RequestFactory

from app.models.custom import CustomProxyUploadedFile
from app.models.site import FileFieldObject
from paper_uploads.exceptions import InvalidContentType
from paper_uploads.views.file import DeleteFileView, UploadFileView


class TestUploadFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomProxyUploadedFile, for_concrete_model=False)

        storage.user = User.objects.create_user(username="jon", email="jon@mail.com", password="password")
        permission = Permission.objects.get(name="Can upload files")
        storage.user.user_permissions.add(permission)

        storage.view = UploadFileView()
        yield

    def test_get_instance(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "app",
            "paperOwnerModelName": "filefieldobject",
            "paperOwnerFieldName": "file_custom"
        })
        request.user = storage.user
        storage.view.setup(request)
        instance = storage.view.get_instance()

        assert isinstance(instance, CustomProxyUploadedFile)
        assert instance.pk is None
        assert instance.get_owner_field() is FileFieldObject._meta.get_field("file_custom")

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(FileFieldObject, for_concrete_model=False)

        request = RequestFactory().post("/", data={
            "paperContentType": content_type.pk,
            "paperOwnerAppLabel": "app",
            "paperOwnerModelName": "filefieldobject",
            "paperOwnerFieldName": "file_custom"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(InvalidContentType):
            storage.view.get_instance()

    def test_validation_errors(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "app",
            "paperOwnerModelName": "filefieldobject",
            "paperOwnerFieldName": "file_extensions"
        })
        request.user = storage.user
        storage.view.setup(request)

        with pytest.raises(ValidationError, match="has an invalid extension"):
            storage.view.handle(request, ContentFile(b'', name="dummy.exe"))

    def test_success(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "paperOwnerAppLabel": "app",
            "paperOwnerModelName": "filefieldobject",
            "paperOwnerFieldName": "file_extensions"
        })
        request.user = storage.user
        storage.view.setup(request)
        response = storage.view.handle(request, ContentFile(b'Hello, dude', name="dummy.txt"))

        assert isinstance(response, JsonResponse)
        assert json.loads(response.content)["name"] == "dummy"


class TestDeleteFileView:
    @staticmethod
    def init_class(storage):
        storage.content_type = ContentType.objects.get_for_model(CustomProxyUploadedFile, for_concrete_model=False)

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

        assert file_model is CustomProxyUploadedFile

    def test_invalid_content_type(self, storage):
        content_type = ContentType.objects.get_for_model(FileFieldObject, for_concrete_model=False)

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
        response = storage.view.handle(request)

        assert isinstance(response, JsonResponse)
        assert json.loads(response.content)["errors"][0] == "Invalid ID"

    def test_object_not_found(self, storage):
        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": 9999
        })
        request.user = storage.user
        storage.view.setup(request)
        response = storage.view.handle(request)

        assert isinstance(response, JsonResponse)
        assert json.loads(response.content)["errors"][0] == "Object not found"

    def test_success(self, storage):
        file = CustomProxyUploadedFile(
            pk=5472
        )
        file.set_owner_from(FileFieldObject._meta.get_field("file_custom"))
        file.save()

        request = RequestFactory().post("/", data={
            "paperContentType": storage.content_type.pk,
            "pk": 5472
        })
        request.user = storage.user
        storage.view.setup(request)
        response = storage.view.handle(request)

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200
        assert json.loads(response.content) == {}

        file.delete_file()
        file.delete()
