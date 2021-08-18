from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from .. import exceptions
from ..forms.dialogs.image import UploadedImageDialog
from ..helpers import run_validators
from ..logging import logger
from ..models.base import FileResource
from . import helpers
from .base import ChangeFileViewBase, DeleteFileViewBase, UploadFileViewBase


class UploadFileView(UploadFileViewBase):
    def handle(self, request, file: UploadedFile):
        content_type_id = request.POST.get("paperContentType")
        model_class = helpers.get_model_class(content_type_id, FileResource)
        instance = model_class(
            owner_app_label=request.POST.get("paperOwnerAppLabel"),
            owner_model_name=request.POST.get("paperOwnerModelName"),
            owner_fieldname=request.POST.get("paperOwnerFieldName"),
        )

        try:
            instance.attach_file(file)
        except exceptions.UnsupportedFileError as e:
            return self.error_response(e.message)

        try:
            instance.full_clean()
            owner_field = instance.get_owner_field()
            if owner_field is not None:
                run_validators(file, owner_field.validators)
        except Exception:
            instance.delete_file()
            raise

        instance.save()
        return self.success_response(instance.as_dict())


class DeleteFileView(DeleteFileViewBase):
    def handle(self, request):
        content_type_id = request.POST.get("paperContentType")
        model_class = helpers.get_model_class(content_type_id, FileResource)
        pk = request.POST.get("pk")

        try:
            instance = helpers.get_instance(model_class, pk)
        except exceptions.InvalidObjectId:
            logger.exception("Error")
            return self.error_response(_("Invalid ID"))
        except ObjectDoesNotExist:
            logger.exception("Error")
            return self.error_response(_("Object not found"))
        except MultipleObjectsReturned:
            logger.exception("Error")
            return self.error_response(_("Multiple objects returned"))

        instance.delete()
        return self.success_response()


class ChangeFileView(ChangeFileViewBase):
    form_class = UploadedImageDialog
    template_name = "paper_uploads/dialogs/image.html"

    def get_instance(self, request, *args, **kwargs):
        content_type_id = self.request.GET.get("paperContentType")
        model_class = helpers.get_model_class(content_type_id, FileResource)
        pk = self.request.GET.get("pk")

        try:
            return helpers.get_instance(model_class, pk)
        except exceptions.InvalidObjectId:
            raise exceptions.AjaxFormError(_("Invalid ID"))
        except ObjectDoesNotExist:
            raise exceptions.AjaxFormError(_("Object not found"))
        except MultipleObjectsReturned:
            raise exceptions.AjaxFormError(_("Multiple objects returned"))
