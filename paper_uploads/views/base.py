import os
import shutil
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Union
from uuid import UUID

from django.conf import settings
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ImproperlyConfigured,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    ValidationError,
)
from django.core.files.uploadedfile import UploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.utils.decorators import method_decorator
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormMixin

from .. import exceptions
from ..files import TemporaryUploadedFile
from ..logging import logger
from ..models.base import Resource


class AjaxView(View):
    @staticmethod
    def success_response(data: Optional[Dict[str, Any]] = None) -> JsonResponse:
        data = data or {}
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
        elif isinstance(errors, Promise):
            errors = [str(errors)]

        data = {
            "errors": errors,
        }
        data.update(extra_data)
        return JsonResponse(data)

    @classmethod
    def wrap(cls, func):
        def inner(*args, **kwargs) -> HttpResponse:
            try:
                return func(*args, **kwargs)
            except exceptions.InvalidContentType as e:
                logger.exception("Error")
                return cls.error_response(_("Invalid ContentType: %s") % e.value)
            except exceptions.InvalidObjectId as e:
                logger.exception("Error")
                return cls.error_response(_("Invalid ID: %s") % e.value)
            except exceptions.InvalidItemType as e:
                logger.exception("Error")
                return cls.error_response(_("Invalid itemType: %s") % e.value)
            except ObjectDoesNotExist:
                logger.exception("Error")
                return cls.error_response(_("Object not found"))
            except MultipleObjectsReturned:
                logger.exception("Error")
                return cls.error_response(_("Multiple objects returned"))
            except ValidationError as e:
                messages = cls.get_exception_messages(e)
                logger.debug(messages)
                return cls.error_response(messages)
            except Exception as e:
                logger.exception("Error")
                if hasattr(e, "args"):
                    message = "{}: {}".format(type(e).__name__, e.args[0])
                else:
                    message = type(e).__name__
                return cls.error_response(message)

        return inner


class UploadFileViewBase(AjaxView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
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
            return self.wrap(self.handle)(file)
        except exceptions.UnsupportedResource as e:
            return self.error_response(e.message)
        finally:
            file.close()

    def upload_chunk(self, request: WSGIRequest) -> UploadedFile:
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

    def handle(self, file: UploadedFile) -> HttpResponse:
        raise NotImplementedError


class DeleteFileViewBase(AjaxView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.has_perm("paper_uploads.delete"):
            return self.error_response(_("Access denied"))
        return self.wrap(self.handle)()

    def handle(self) -> HttpResponse:
        raise NotImplementedError


class ChangeFileViewBase(FormMixin, AjaxView):
    template_name = None
    http_method_names = ["get", "post"]

    def get_template_name(self) -> str:
        if self.template_name is None:
            raise ImproperlyConfigured(
                "{} requires either a definition of "
                "'template_name' or an implementation of 'get_template_name()'".format(
                    type(self).__name__
                )
            )
        else:
            return self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "action": self.request.get_full_path(),
        })
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_instance()
        return kwargs

    def get_instance(self):
        raise NotImplementedError

    def get(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.has_perm("paper_uploads.change"):
            return self.error_response(_("Access denied"))

        form_response = self.wrap(self.render_form)()
        if isinstance(form_response, HttpResponse):
            return form_response

        return self.success_response({
            "form": form_response
        })

    def render_form(self, **kwargs) -> str:
        context = self.get_context_data(**kwargs)
        template_name = self.get_template_name()
        return loader.render_to_string(template_name, context, request=self.request)

    def post(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.has_perm("paper_uploads.change"):
            return self.error_response(_("Access denied"))

        return self.wrap(self.validate_form)()

    def validate_form(self) -> HttpResponse:
        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)

        return self.form_valid(form)

    def form_valid(self, form) -> HttpResponse:
        try:
            instance = form.save()
        except FileNotFoundError as e:
            error = _("File not found: %s") % e.args[0] if e.args else "???"
            logger.debug(error)
            return self.error_response(error)

        return self.success(instance)

    def form_invalid(self, form) -> HttpResponse:
        return JsonResponse({
            "form_errors": form.errors.get_json_data()
        })

    def success(self, instance: Resource) -> HttpResponse:
        return self.success_response(instance.as_dict())
