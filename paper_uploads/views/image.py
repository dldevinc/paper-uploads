import posixpath
from django.db import transaction
from django.template import loader
from django.core.files import File
from django.views.generic import FormView
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import filesizeformat
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from ..forms.dialogs.image import UploadedImageDialog
from ..models import UploadedImageBase
from .. import exceptions
from .. import utils
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
        utils.logger.exception('Error')
        return helpers.error_response('Invalid UUID')
    except exceptions.InvalidChunking:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid chunking', prevent_retry=False)
    else:
        if not isinstance(file, File):
            file = File(file, name=basename)

    # Определение модели файла
    content_type_id = request.POST.get('paperContentType')
    try:
        model_class = helpers.get_model_class(content_type_id, base_class=UploadedImageBase)
    except exceptions.InvalidContentType:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid content type')

    # Определение модели владельца файла
    owner_app_label = request.POST.get('paperOwnerAppLabel')
    owner_model_name = request.POST.get('paperOwnerModelName')
    try:
        owner_content_type = ContentType.objects.get(
            app_label=owner_app_label,
            model=owner_model_name
        )
    except ContentType.DoesNotExist:
        utils.logger.exception('Invalid owner content type: %s.%s' % (owner_app_label, owner_model_name))
        return helpers.error_response('Invalid owner content type')

    owner_field_name = request.POST.get('paperOwnerFieldname')

    try:
        with transaction.atomic():
            instance = model_class(
                file=file,
                owner_ct=owner_content_type,
                owner_fieldname=owner_field_name
            )
            instance.full_clean()
            instance.save()
    except ValidationError as e:
        message = helpers.exception_response(e)
        utils.logger.debug(message)
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
        model_class = helpers.get_model_class(content_type_id, base_class=UploadedImageBase)
    except exceptions.InvalidContentType:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid content type')

    try:
        instance = helpers.get_instance(model_class, instance_id)
    except exceptions.InvalidObjectId:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid ID')
    except ObjectDoesNotExist:
        utils.logger.exception('Error')
        return helpers.error_response('Object not found')
    except MultipleObjectsReturned:
        utils.logger.exception('Error')
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
            model_class = helpers.get_model_class(content_type_id, base_class=UploadedImageBase)
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
        return helpers.success_response({
            'instance_id': self.instance.pk,
            'name': self.instance.name,
            'url': self.instance.file.url,
            'file_info': '({width}x{height}, {size})'.format(
                width=self.instance.width,
                height=self.instance.height,
                size=filesizeformat(self.instance.size)
            )
        })

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
            utils.logger.exception('Error')
            return helpers.error_response(exc.message)
        return super().get_form(form_class)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return helpers.success_response({
            'form': loader.render_to_string(self.template_name, context, request=request)
        })
