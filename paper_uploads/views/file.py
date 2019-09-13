import posixpath
from django.db import transaction
from django.template import loader
from django.core.files import File
from django.views.generic import FormView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from ..forms.dialogs.file import UploadedFileDialog
from ..models import UploadedFileBase
from ..logging import logger
from .. import exceptions
from . import helpers


@csrf_exempt
@require_http_methods(["POST"])
def upload(request):
    if not request.user.has_perm('paper_uploads.upload'):
        return helpers.error_response('Access denied')

    qqfilename = request.POST.get('qqfilename')
    basename = posixpath.basename(qqfilename)

    try:
        file = helpers.read_file(request)
    except exceptions.ContinueUpload:
        return helpers.success_response()
    except exceptions.InvalidUUID:
        logger.exception('Error')
        return helpers.error_response('Invalid UUID')
    except exceptions.InvalidChunking:
        logger.exception('Error')
        return helpers.error_response('Invalid chunking', prevent_retry=False)
    else:
        if not isinstance(file, File):
            file = File(file, name=basename)

    # Определение модели файла
    content_type_id = request.POST.get('paperContentType')
    try:
        model_class = helpers.get_model_class(content_type_id, base_class=UploadedFileBase)
    except exceptions.InvalidContentType:
        logger.exception('Error')
        return helpers.error_response('Invalid content type')

    try:
        with transaction.atomic():
            instance = model_class(
                file=file,
                owner_app_label=request.POST.get('paperOwnerAppLabel'),
                owner_model_name=request.POST.get('paperOwnerModelName'),
                owner_fieldname=request.POST.get('paperOwnerFieldname')
            )
            instance.full_clean()
            instance.save()
    except ValidationError as e:
        message = helpers.exception_response(e)
        logger.debug(message)
        return helpers.error_response(message)

    return helpers.success_response(instance.as_dict())


@csrf_exempt
@require_http_methods(["POST"])
def delete(request):
    if not request.user.has_perm('paper_uploads.delete'):
        return helpers.error_response('Access denied')

    content_type_id = request.POST.get('paperContentType')
    instance_id = request.POST.get('instance_id')

    try:
        model_class = helpers.get_model_class(content_type_id, base_class=UploadedFileBase)
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
    template_name = 'paper_uploads/dialogs/file.html'
    permission_required = 'paper_uploads.change'
    form_class = UploadedFileDialog
    instance = None

    def get_instance(self):
        content_type_id = self.request.GET.get('paperContentType')
        instance_id = self.request.GET.get('instance_id')

        try:
            model_class = helpers.get_model_class(content_type_id, base_class=UploadedFileBase)
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
        return helpers.success_response({
            'form': loader.render_to_string(self.template_name, context, request=request)
        })
