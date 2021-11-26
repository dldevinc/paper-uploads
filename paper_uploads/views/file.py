from typing import Any, Type

from django.core.files.uploadedfile import UploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils.module_loading import import_string

from ..helpers import run_validators
from ..models.base import FileResource
from ..models.mixins import BacklinkModelMixin, EditableResourceMixin
from . import helpers
from .base import ChangeFileViewBase, DeleteFileViewBase, UploadFileViewBase


class UploadFileView(UploadFileViewBase):
    def get_file_model(self) -> Type[FileResource]:
        content_type_id = self.request.POST.get("paperContentType")
        return helpers.get_model_class(content_type_id, FileResource)

    def get_instance(self) -> FileResource:
        file_model = self.get_file_model()
        return file_model(
            owner_app_label=self.request.POST.get("paperOwnerAppLabel"),
            owner_model_name=self.request.POST.get("paperOwnerModelName"),
            owner_fieldname=self.request.POST.get("paperOwnerFieldName"),
        )

    def handle(self, request: WSGIRequest, file: UploadedFile) -> HttpResponse:
        instance = self.get_instance()

        owner_field = None
        if isinstance(instance, BacklinkModelMixin):
            owner_field = instance.get_owner_field()

        instance.attach_file(file)

        try:
            instance.full_clean()
            if owner_field is not None:
                run_validators(file, owner_field.validators)
        except Exception:
            instance.delete_file()
            raise

        instance.save()

        return self.success(instance)

    def success(self, instance: FileResource) -> HttpResponse:
        return self.success_response(instance.as_dict())


class DeleteFileView(DeleteFileViewBase):
    def get_file_model(self) -> Type[FileResource]:
        content_type_id = self.request.POST.get("paperContentType")
        return helpers.get_model_class(content_type_id, FileResource)

    def get_file_id(self) -> Any:
        return self.request.POST.get("pk")

    def handle(self, request: WSGIRequest) -> HttpResponse:
        file_model = self.get_file_model()
        file_id = self.get_file_id()
        instance = helpers.get_instance(file_model, file_id)
        instance.delete()
        return self.success()

    def success(self) -> HttpResponse:
        return self.success_response()


class ChangeFileView(ChangeFileViewBase):
    template_name = "paper_uploads/dialogs/file.html"

    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class

        if isinstance(self.instance, EditableResourceMixin):
            return import_string(self.instance.change_form_class)

    def get_file_model(self) -> Type[FileResource]:
        content_type_id = self.request.GET.get("paperContentType")
        return helpers.get_model_class(content_type_id, FileResource)

    def get_file_id(self) -> Any:
        return self.request.GET.get("pk")

    def get_instance(self, request: WSGIRequest, *args, **kwargs):
        file_model = self.get_file_model()
        file_id = self.get_file_id()
        return helpers.get_instance(file_model, file_id)
