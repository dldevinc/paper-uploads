import os
import shutil
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Union
from uuid import UUID

from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse
from django.template import loader
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin

from .. import exceptions
from ..files import TemporaryUploadedFile
from ..logging import logger


class AjaxView(View):
    @staticmethod
    def success_response(data: Optional[Dict[str, Any]] = None) -> JsonResponse:
        data = data or {}
        data["success"] = True
        return JsonResponse(data)

    @staticmethod
    def get_exception_messages(exception: ValidationError) -> List[str]:
        messages = []  # type: List[str]
        for msg in exception:
            if isinstance(msg, tuple):
                field, errors = msg
                if field == NON_FIELD_ERRORS:
                    for error in reversed(errors):
                        messages.insert(0, error)
                else:
                    messages.extend("'{}': {}".format(field, error) for error in errors)
            else:
                messages.append(msg)
        return messages

    @staticmethod
    def error_response(
        errors: Union[str, Iterable[str]] = "", **extra_data
    ) -> JsonResponse:
        if not errors:
            errors = []
        elif isinstance(errors, str):
            errors = [errors]

        data = {
            "success": False,
            "errors": errors,
        }
        data.update(extra_data)
        return JsonResponse(data)


class ActionView(AjaxView):
    def perform_action(self, request, *args, **kwargs):
        try:
            return self.handle(request, *args, **kwargs)
        except exceptions.InvalidContentType:
            logger.exception("Error")
            return self.error_response(_("Invalid ContentType"))
        except ValidationError as e:
            messages = self.get_exception_messages(e)
            logger.debug(messages)
            return self.error_response(messages)
        except Exception as e:
            logger.exception("Error")
            if hasattr(e, "args"):
                message = "{}: {}".format(type(e).__name__, e.args[0])
            else:
                message = type(e).__name__
            return self.error_response(message)

    def handle(self, *args, **kwargs):
        raise NotImplementedError


class UploadFileViewBase(ActionView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("paper_uploads.upload"):
            return self.error_response(_("Access denied"))

        try:
            file = self.upload_chunk(request)
        except exceptions.ContinueUpload:
            return self.success_response()
        except exceptions.UncompleteUpload:
            return self.error_response(preventRetry=True)
        except exceptions.InvalidUUID as e:
            logger.exception("Error")
            return self.error_response(_("Invalid UUID: %s") % e.value, preventRetry=True)
        except exceptions.InvalidChunking:
            logger.exception("Error")
            return self.error_response(_("Invalid chunking"), preventRetry=True)

        try:
            return self.perform_action(request, file)
        finally:
            file.close()

    def upload_chunk(self, request) -> UploadedFile:
        try:
            chunk_index = int(request.POST["paperChunkIndex"])
            total_chunks = int(request.POST["paperTotalChunkCount"])
        except KeyError:
            # small file, no chunks
            chunk_index = 0
            total_chunks = 1
        except (ValueError, TypeError):
            raise exceptions.InvalidChunking

        uuid = request.POST.get("paperUUID")
        try:
            uid = UUID(uuid)
        except (AttributeError, ValueError):
            raise exceptions.InvalidUUID(uuid)

        tempdir = request.session.get("paper_uploads_tempdir")
        if tempdir is None or not os.path.isdir(tempdir):
            if request.user.pk is not None:
                tempdir_suffix = ".user_{}".format(request.user.pk)
            else:
                tempdir_suffix = None

            tempdir = tempfile.mkdtemp(
                prefix="paper_uploads.",
                suffix=tempdir_suffix,
                dir=settings.FILE_UPLOAD_TEMP_DIR
            )
            request.session["paper_uploads_tempdir"] = tempdir

        tempfilepath = os.path.join(tempdir, str(uid))
        file = request.FILES.get("file")
        if file is None:
            # случается при отмене загрузки на медленном интернете
            if os.path.isfile(tempfilepath):
                os.unlink(tempfilepath)
            raise exceptions.UncompleteUpload

        if total_chunks > 1:
            with open(tempfilepath, "a+b") as fp:
                shutil.copyfileobj(file, fp)

            if chunk_index < total_chunks - 1:
                raise exceptions.ContinueUpload

            file = TemporaryUploadedFile(
                open(tempfilepath, "rb"),
                name=os.path.basename(file.name),
                size=os.path.getsize(tempfilepath)
            )
        return file


class DeleteFileViewBase(ActionView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("paper_uploads.delete"):
            return self.error_response(_("Access denied"))
        return self.perform_action(request, *args, **kwargs)


class ChangeFileViewBase(TemplateResponseMixin, FormMixin, AjaxView):
    http_method_names = ["get", "post"]
    instance = None

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm("paper_uploads.change"):
            return self.error_response(_("Access denied"))

        try:
            self.instance = self.get_instance(request, *args, **kwargs)
        except exceptions.AjaxFormError as exc:
            logger.exception("Error")
            return self.error_response(exc.message)

        context = self.get_context_data(**kwargs)
        return self.success_response({
            "form": loader.render_to_string(self.template_name, context, request=request)
        })

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("paper_uploads.change"):
            return self.error_response(_("Access denied"))

        try:
            self.instance = self.get_instance(request, *args, **kwargs)
        except exceptions.AjaxFormError as exc:
            logger.exception("Error")
            return self.error_response(exc.message)

        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)

        try:
            return self.form_valid(form)
        except ValidationError as e:
            messages = self.get_exception_messages(e)
            logger.debug(messages)
            return self.error_response(messages)
        except exceptions.FileNotFoundError as e:
            error = _("File not found: %s") % e.name
            logger.debug(error)
            return self.error_response(error)
        except exceptions.AjaxFormError as exc:
            logger.exception("Error")
            return self.error_response(exc.message)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "action": self.request.get_full_path(),
            "instance": self.instance,
        })
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.instance
        return kwargs

    def get_instance(self, request, *args, **kwargs):
        raise NotImplementedError

    def form_valid(self, form):
        form.save()
        return self.success_response(self.instance.as_dict())  # noqa: F821

    def form_invalid(self, form):
        return JsonResponse({
            "form_errors": form.errors.get_json_data()
        })
