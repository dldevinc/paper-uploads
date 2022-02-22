from typing import Any, Type, cast

from django.core.files.uploadedfile import UploadedFile
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

    def handle(self, file: UploadedFile) -> HttpResponse:
        instance = self.get_instance()

        owner_field = None
        if isinstance(instance, BacklinkModelMixin):
            owner_field = instance.get_owner_field()

        instance.attach(file)

        try:
            instance.full_clean()
            if owner_field is not None:
                run_validators(file, owner_field.validators)
        except Exception:
            instance.delete_file()
            raise

        instance.save()

        if not file.closed:
            file.close()

        return self.success(instance)

    def success(self, instance: FileResource) -> HttpResponse:
        return self.success_response(instance.as_dict())


class DeleteFileView(DeleteFileViewBase):
    def get_file_model(self) -> Type[FileResource]:
        content_type_id = self.request.POST.get("paperContentType")
        return helpers.get_model_class(content_type_id, FileResource)

    def get_file_id(self) -> Any:
        return self.request.POST.get("pk")

    def get_instance(self) -> FileResource:
        file_model = self.get_file_model()
        file_id = self.get_file_id()
        return cast(FileResource, helpers.get_instance(file_model, file_id))

    def handle(self) -> HttpResponse:
        instance = self.get_instance()
        instance.delete()
        return self.success()

    def success(self) -> HttpResponse:
        return self.success_response()


class ChangeFileView(ChangeFileViewBase):
    template_name = "paper_uploads/dialogs/image.html"

    def get_file_model(self) -> Type[FileResource]:
        content_type_id = self.request.GET.get("paperContentType")
        return helpers.get_model_class(content_type_id, FileResource)

    def get_file_id(self) -> Any:
        return self.request.GET.get("pk")

    def get_instance(self) -> FileResource:
        file_model = self.get_file_model()
        file_id = self.get_file_id()
        return cast(FileResource, helpers.get_instance(file_model, file_id))

    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class

        file_model = self.get_file_model()
        if issubclass(file_model, EditableResourceMixin):
            return import_string(file_model.change_form_class)
