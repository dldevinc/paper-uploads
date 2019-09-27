import posixpath
from django.db import transaction
from django.template import loader
from django.core.files import File
from django.views.generic import FormView
from django.views.decorators.csrf import csrf_exempt
from django.utils.module_loading import import_string
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from ..models import GalleryItemBase, GalleryBase
from ..utils import run_validators
from ..logging import logger
from .. import exceptions
from .. import signals
from . import helpers


def detect_file_type(collection_cls, file):
    for item_type, item_type_field in collection_cls.item_types.items():
        if item_type_field.model.check_file(file):
            return item_type
    return None


@csrf_exempt
@require_http_methods(["POST"])
def delete_collection(request):
    if not request.user.has_perm('paper_uploads.delete'):
        return helpers.error_response('Access denied')

    content_type_id = request.POST.get('paperCollectionContentType')
    try:
        collection_cls = helpers.get_model_class(content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        logger.exception('Error')
        return helpers.error_response('Invalid content type')

    collection_id = request.POST.get('collectionId')
    try:
        instance = helpers.get_instance(collection_cls, collection_id)
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
        logger.exception('Error')
        return helpers.error_response('Invalid UUID')
    except exceptions.InvalidChunking:
        logger.exception('Error')
        return helpers.error_response('Invalid chunking', prevent_retry=False)
    else:
        if not isinstance(file, File):
            file = File(file, name=basename)

    # Определение модели галереи
    content_type_id = request.POST.get('paperCollectionContentType')
    try:
        collection_cls = helpers.get_model_class(content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        logger.exception('Error')
        return helpers.error_response('Invalid content type')

    # Определение типа элемента галереи
    item_type = detect_file_type(collection_cls, file)
    if item_type is None:
        return helpers.error_response('Unsupported file')

    # Получение объекта галереи
    collection_id = request.POST.get('collectionId')
    try:
        collection = helpers.get_instance(collection_cls, collection_id)
    except exceptions.InvalidObjectId:
        # создадим новую галерею
        collection = None
    except ObjectDoesNotExist:
        logger.exception('Error')
        return helpers.error_response('Collection not found')
    except MultipleObjectsReturned:
        logger.exception('Error')
        return helpers.error_response('Multiple objects returned')

    try:
        with transaction.atomic():
            if collection is None:
                # Создание галереи
                collection = collection_cls._meta.default_manager.create(
                    owner_app_label=request.POST.get('paperOwnerAppLabel'),
                    owner_model_name=request.POST.get('paperOwnerModelName'),
                    owner_fieldname=request.POST.get('paperOwnerFieldname')
                )

            item_type_field = collection_cls.item_types[item_type]
            instance = item_type_field.model(
                content_type_id=content_type_id,
                object_id=collection.pk,
                item_type=item_type,
                file=file,
                name=filename,
                size=file.size
            )
            instance.full_clean()
            run_validators(file, item_type_field.validators)
            instance.save()
    except ValidationError as e:
        messages = helpers.get_exception_messages(e)
        logger.debug(messages)
        return helpers.error_response(messages)
    except Exception as e:
        logger.exception('Error')
        if hasattr(e, 'args'):
            message = '{}: {}'.format(type(e).__name__, e.args[0])
        else:
            message = type(e).__name__
        return helpers.error_response(message)

    collection.refresh_from_db(fields=['cover_id'])
    return helpers.success_response({
        **instance.as_dict(),
        'cover': collection.cover_id,
    })


@csrf_exempt
@require_http_methods(["POST"])
def delete_item(request):
    if not request.user.has_perm('paper_uploads.delete'):
        return helpers.error_response('Access denied')

    content_type_id = request.POST.get('paperCollectionContentType')
    try:
        collection_cls = helpers.get_model_class(content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        logger.exception('Error')
        return helpers.error_response('Invalid content type')

    item_type = request.POST.get('item_type')
    for name, field in collection_cls.item_types.items():
        if item_type == name:
            model_class = field.model
            break
    else:
        return helpers.error_response('Invalid item type')

    instance_id = request.POST.get('instance_id')
    try:
        instance = helpers.get_instance(model_class, instance_id)
    except exceptions.InvalidObjectId:
        logger.exception('Error')
        return helpers.error_response('Invalid ID')
    except ObjectDoesNotExist:
        # silently skip
        return helpers.success_response()
    except MultipleObjectsReturned:
        logger.exception('Error')
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

    content_type_id = request.POST.get('paperCollectionContentType')
    try:
        collection_cls = helpers.get_model_class(content_type_id, base_class=GalleryBase)
    except exceptions.InvalidContentType:
        logger.exception('Error')
        return helpers.error_response('Invalid content type')

    collection_id = request.POST.get('collectionId')
    try:
        instance = helpers.get_instance(collection_cls, collection_id)
    except exceptions.InvalidObjectId:
        logger.exception('Error')
        return helpers.error_response('Invalid ID')
    except ObjectDoesNotExist:
        logger.exception('Error')
        return helpers.error_response('Object not found')
    except MultipleObjectsReturned:
        logger.exception('Error')
        return helpers.error_response('Multiple objects returned')

    order_string = request.POST.get('order', '')
    try:
        item_ids = (int(pk) for pk in order_string.split(','))
    except ValueError:
        logger.exception('Error')
        return helpers.error_response('Invalid order')

    with transaction.atomic():
        for index, item_id in enumerate(item_ids):
            if item_id in set(instance.items.values_list('pk', flat=True)):
                GalleryItemBase.objects.filter(pk=item_id).update(order=index)
            else:
                GalleryItemBase.objects.filter(pk=item_id).update(order=2**32 - 1)

    signals.collection_reordered.send(collection_cls, instance=instance)
    return helpers.success_response()


class ChangeView(PermissionRequiredMixin, FormView):
    template_name = 'paper_uploads/dialogs/collection.html'
    permission_required = 'paper_uploads.change'
    instance = None

    def get_form_class(self):
        return import_string(self.instance.FORM_CLASS)

    def get_instance(self):
        content_type_id = self.request.GET.get('paperCollectionContentType')
        try:
            collection_cls = helpers.get_model_class(content_type_id, base_class=GalleryBase)
        except exceptions.InvalidContentType:
            logger.exception('Error')
            return helpers.error_response('Invalid content type')

        item_type = self.request.GET.get('item_type')
        for name, field in collection_cls.item_types.items():
            if item_type == name:
                model_class = field.model
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
            logger.exception('Error')
            return helpers.error_response(exc.message)
        return super().get_form(form_class)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return helpers.success_response({
            'form': loader.render_to_string(self.template_name, context, request=request)
        })
