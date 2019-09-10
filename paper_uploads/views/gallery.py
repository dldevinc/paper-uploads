import posixpath
from django.db import transaction
from django.template import loader
from django.core.files import File
from django.views.generic import FormView
from django.views.decorators.csrf import csrf_exempt
from django.utils.module_loading import import_string
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from ..models import GalleryItemBase, GalleryBase
from .. import exceptions
from .. import signals
from .. import utils
from . import helpers


@csrf_exempt
@require_http_methods(["POST"])
def delete_gallery(request):
    if not request.user.has_perm('paper_uploads.delete'):
        return helpers.error_response('Access denied')

    gallery_content_type_id = request.POST.get('paperGalleryContentType')
    try:
        gallery_cls = helpers.get_model_class(gallery_content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid gallery content type')

    gallery_id = request.POST.get('gallery_id')
    try:
        instance = helpers.get_instance(gallery_cls, gallery_id)
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


@csrf_exempt
@require_http_methods(["POST"])
def upload_item(request):
    if not request.user.has_perm('paper_uploads.upload'):
        return helpers.error_response('Access denied')

    qqfilename = request.POST.get('qqfilename')
    basename = posixpath.basename(qqfilename)
    filename, ext = posixpath.splitext(basename)

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

    # Определение модели галереи
    gallery_content_type_id = request.POST.get('paperGalleryContentType')
    try:
        gallery_cls = helpers.get_model_class(gallery_content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid gallery content type')

    # Определение типа элемента галереи
    item_type = gallery_cls.guess_item_type(file)
    if item_type is None:
        return helpers.error_response('Unsupported file type')

    # Получение объекта галереи
    gallery_id = request.POST.get('gallery_id')
    try:
        gallery = helpers.get_instance(gallery_cls, gallery_id)
    except exceptions.InvalidObjectId:
        # создадим новую галерею
        gallery = None
    except ObjectDoesNotExist:
        utils.logger.exception('Error')
        return helpers.error_response('Gallery not found')
    except MultipleObjectsReturned:
        utils.logger.exception('Error')
        return helpers.error_response('Multiple objects returned')

    model_class = gallery_cls.ALLOWED_ITEM_TYPES[item_type]
    owner_field_name = request.POST.get('paperOwnerFieldname')

    # Определение модели владельца файла
    owner_content_type = None
    if gallery is None:
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

    try:
        with transaction.atomic():
            if gallery is None:
                # Создание галереи
                gallery = gallery_cls._meta.default_manager.create(
                    owner_ct=owner_content_type,
                    owner_fieldname=owner_field_name
                )

            instance = model_class(
                content_type_id=gallery_content_type_id,
                object_id=gallery.pk,
                item_type=item_type,
                file=file,
                name=filename,
                size=file.size
            )
            instance.full_clean()
            instance.save()
    except ValidationError as e:
        message = helpers.exception_response(e)
        utils.logger.debug(message)
        return helpers.error_response(message)
    except Exception as e:
        utils.logger.exception('Error')
        if hasattr(e, 'args'):
            message = '{}: {}'.format(type(e).__name__, e.args[0])
        else:
            message = type(e).__name__
        return helpers.error_response(message)

    gallery.refresh_from_db(fields=['cover_id'])
    return helpers.success_response({
        **instance.as_dict(),
        'cover': gallery.cover_id,
    })


@csrf_exempt
@require_http_methods(["POST"])
def delete_item(request):
    if not request.user.has_perm('paper_uploads.delete'):
        return helpers.error_response('Access denied')

    gallery_content_type_id = request.POST.get('paperGalleryContentType')
    try:
        gallery_cls = helpers.get_model_class(gallery_content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid gallery content type')

    item_type = request.POST.get('item_type')
    for key, model in gallery_cls.ALLOWED_ITEM_TYPES.items():
        if item_type == key:
            model_class = model
            break
    else:
        return helpers.error_response('Invalid item type')

    instance_id = request.POST.get('instance_id')
    try:
        instance = helpers.get_instance(model_class, instance_id)
    except exceptions.InvalidObjectId:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid ID')
    except ObjectDoesNotExist:
        # silently skip
        return helpers.success_response()
    except MultipleObjectsReturned:
        utils.logger.exception('Error')
        return helpers.error_response('Multiple objects returned')
    else:
        instance.delete()
        instance.gallery.refresh_from_db(fields=['cover_id'])
        return helpers.success_response({
            'cover': instance.gallery.cover_id,
        })


@csrf_exempt
@require_http_methods(["POST"])
def sort_items(request):
    if not request.user.has_perm('paper_uploads.change'):
        return helpers.error_response('Access denied')

    gallery_content_type_id = request.POST.get('paperGalleryContentType')
    try:
        gallery_cls = helpers.get_model_class(gallery_content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid gallery content type')

    gallery_id = request.POST.get('gallery_id')
    try:
        instance = helpers.get_instance(gallery_cls, gallery_id)
    except exceptions.InvalidObjectId:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid ID')
    except ObjectDoesNotExist:
        utils.logger.exception('Error')
        return helpers.error_response('Object not found')
    except MultipleObjectsReturned:
        utils.logger.exception('Error')
        return helpers.error_response('Multiple objects returned')

    order_string = request.POST.get('order', '')
    try:
        item_ids = (int(pk) for pk in order_string.split(','))
    except ValueError:
        utils.logger.exception('Error')
        return helpers.error_response('Invalid order')

    gallery_items = set(instance.items.values_list('pk', flat=True))
    with transaction.atomic():
        for index, item_id in enumerate(item_ids):
            if item_id in gallery_items:
                GalleryItemBase.objects.filter(pk=item_id).update(order=index)
            else:
                GalleryItemBase.objects.filter(pk=item_id).update(order=2**32 - 1)

    signals.gallery_reordered.send(gallery_cls, instance=instance)
    return helpers.success_response()


class ChangeView(PermissionRequiredMixin, FormView):
    template_name = 'paper_uploads/dialogs/gallery.html'
    permission_required = 'paper_uploads.change'
    instance = None

    def get_form_class(self):
        return import_string(self.instance.FORM_CLASS)

    def get_instance(self):
        gallery_content_type_id = self.request.GET.get('paperGalleryContentType')
        try:
            gallery_cls = helpers.get_model_class(gallery_content_type_id, base_class=GalleryBase)
        except exceptions.InvalidContentType:
            utils.logger.exception('Error')
            return helpers.error_response('Invalid gallery content type')

        item_type = self.request.GET.get('item_type')
        for key, model in gallery_cls.ALLOWED_ITEM_TYPES.items():
            if item_type == key:
                model_class = model
                break
        else:
            raise exceptions.AjaxFormError('Invalid item type')

        instance_id = self.request.GET.get('instance_id')
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
            utils.logger.exception('Error')
            return helpers.error_response(exc.message)
        return super().get_form(form_class)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return helpers.success_response({
            'form': loader.render_to_string(self.template_name, context, request=request)
        })
