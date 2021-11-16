from typing import Any, Type

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from .. import exceptions
from ..forms.dialogs.image import UploadedImageDialog
from ..helpers import run_validators
from ..logging import logger
from ..models.base import FileResource
from . import helpers
from .base import ChangeFileViewBase, DeleteFileViewBase, UploadFileViewBase


class UploadFileView(UploadFileViewBase):
    def get_instance(self) -> FileResource:
        content_type_id = self.request.POST.get("paperContentType")
        model_class = helpers.get_model_class(content_type_id, FileResource)
        return model_class(
            owner_app_label=self.request.POST.get("paperOwnerAppLabel"),
            owner_model_name=self.request.POST.get("paperOwnerModelName"),
            owner_fieldname=self.request.POST.get("paperOwnerFieldName"),
        )

    def handle(self, request: WSGIRequest, file: UploadedFile) -> HttpResponse:
        instance = self.get_instance()
        owner_field = instance.get_owner_field()

        try:
            instance.attach_file(file)
        except exceptions.UnsupportedFileError as e:
            return self.error_response(e.message)

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
        model = self.get_file_model()
        pk = self.get_file_id()

        try:
            instance = helpers.get_instance(model, pk)
        except exceptions.InvalidObjectId:
            logger.exception("Error")
            return self.error_response(_("Invalid ID"))
        except ObjectDoesNotExist:
            logger.exception("Error")
            return self.error_response(_("Object not found"))
        except MultipleObjectsReturned:
            logger.exception("Error")
            return self.error_response(_("Multiple objects returned"))
        else:
            instance.delete()

        return self.success()

    def success(self) -> HttpResponse:
        return self.success_response()


class ChangeFileView(ChangeFileViewBase):
    template_name = "paper_uploads/dialogs/image.html"

    def get_form_class(self):
        # compat
        if not hasattr(self.instance, "change_form_class"):
            return UploadedImageDialog

        if isinstance(self.instance.change_form_class, str):
            return import_string(self.instance.change_form_class)
        else:
            return self.instance.change_form_class

    def get_file_model(self) -> Type[FileResource]:
        content_type_id = self.request.GET.get("paperContentType")
        return helpers.get_model_class(content_type_id, FileResource)

    def get_file_id(self) -> Any:
        return self.request.GET.get("pk")

    def get_instance(self, request: WSGIRequest, *args, **kwargs):
        model = self.get_file_model()
        pk = self.get_file_id()

        try:
            return helpers.get_instance(model, pk)
        except exceptions.InvalidObjectId:
            raise exceptions.AjaxFormError(_("Invalid ID"))
        except ObjectDoesNotExist:
            raise exceptions.AjaxFormError(_("Object not found"))
        except MultipleObjectsReturned:
            raise exceptions.AjaxFormError(_("Multiple objects returned"))
