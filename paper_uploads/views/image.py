from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    ValidationError,
)
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView

from .. import exceptions
from ..forms.dialogs.image import UploadedImageDialog
from ..logging import logger
from ..models import FileResource
from ..utils import run_validators
from . import helpers


@csrf_exempt
@require_http_methods(["POST"])
def upload(request):
    if not request.user.has_perm('paper_uploads.upload'):
        return helpers.error_response('Access denied')

    try:
        file = helpers.read_file(request)
    except exceptions.ContinueUpload:
        return helpers.success_response()
    except exceptions.UncompleteUpload:
        return helpers.error_response()
    except exceptions.InvalidUUID:
        logger.exception('Error')
        return helpers.error_response('Invalid UUID')
    except exceptions.InvalidChunking:
        logger.exception('Error')
        return helpers.error_response('Invalid chunking', prevent_retry=False)

    try:
        # Определение модели файла
        content_type_id = request.POST.get('paperContentType')
        try:
            model_class = helpers.get_model_class(
                content_type_id, base_class=FileResource
            )
        except exceptions.InvalidContentType:
            logger.exception('Error')
            return helpers.error_response('Invalid content type')

        instance = model_class(
            owner_app_label=request.POST.get('paperOwnerAppLabel'),
            owner_model_name=request.POST.get('paperOwnerModelName'),
            owner_fieldname=request.POST.get('paperOwnerFieldname'),
        )
        owner_field = instance.get_owner_field()

        try:
            instance.attach_file(file)
            instance.full_clean()
            if owner_field is not None:
                run_validators(file, owner_field.validators)
        except ValidationError as e:
            instance.delete_file()
            messages = helpers.get_exception_messages(e)
            logger.debug(messages)
            return helpers.error_response(messages)

        instance.save()
    finally:
        file.close()
    return helpers.success_response(instance.as_dict())


@csrf_exempt
@require_http_methods(["POST"])
def delete(request):
    if not request.user.has_perm('paper_uploads.delete'):
        return helpers.error_response('Access denied')

    content_type_id = request.POST.get('paperContentType')
    instance_id = request.POST.get('instance_id')

    try:
        model_class = helpers.get_model_class(content_type_id, base_class=FileResource)
    except exceptions.InvalidContentType:
        logger.exception('Error')
        return helpers.error_response('Invalid content type')

    try:
        instance = helpers.get_instance(model_class, instance_id)
    except exceptions.InvalidObjectId:
        logger.exception('Error')
        return helpers.error_response('Invalid ID')
    except ObjectDoesNotExist:
        logger.exception('Error')
        return helpers.error_response('Object not found')
    except MultipleObjectsReturned:
        logger.exception('Error')
        return helpers.error_response('Multiple objects returned')

    instance.delete()
    return helpers.success_response()


class ChangeView(PermissionRequiredMixin, FormView):
    template_name = 'paper_uploads/dialogs/image.html'
    permission_required = 'paper_uploads.change'
    form_class = UploadedImageDialog
    instance = None

    def get_instance(self):
        content_type_id = self.request.GET.get('paperContentType')
        instance_id = self.request.GET.get('instance_id')

        try:
            model_class = helpers.get_model_class(
                content_type_id, base_class=FileResource
            )
        except exceptions.InvalidContentType:
            raise exceptions.AjaxFormError('Invalid content type')

        try:
            return helpers.get_instance(model_class, instance_id)
        except exceptions.InvalidObjectId:
            raise exceptions.AjaxFormError('Invalid ID')
        except ObjectDoesNotExist:
            raise exceptions.AjaxFormError('Object not found')
        except MultipleObjectsReturned:
            raise exceptions.AjaxFormError('Multiple objects returned')

    def form_valid(self, form):
        form.save()
        return helpers.success_response(self.instance.as_dict())

    def form_invalid(self, form):
        return helpers.success_response({
            'form_errors': form.errors.get_json_data()
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'action': self.request.get_full_path(),
            'instance': self.instance,
        })
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.instance
        return kwargs

    def get_form(self, form_class=None):
        try:
            self.instance = self.get_instance()
        except exceptions.AjaxFormError as exc:
            logger.exception('Error')
            return helpers.error_response(exc.message)
        return super().get_form(form_class)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return helpers.success_response(
            {
                'form': loader.render_to_string(
                    self.template_name, context, request=request
                )
            }
        )
