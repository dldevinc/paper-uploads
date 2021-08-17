from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from .. import exceptions, signals
from ..helpers import run_validators
from ..logging import logger
from ..models.collection import CollectionBase, CollectionItemBase
from . import helpers
from .base import ActionView, ChangeFileViewBase, DeleteFileViewBase, UploadFileViewBase


class CreateCollectionView(ActionView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("paper_uploads.upload"):
            return self.error_response(_("Access denied"))
        return self.perform_action(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        content_type_id = request.POST.get("paperCollectionContentType")
        collection_cls = helpers.get_model_class(content_type_id, CollectionBase)
        collection = collection_cls.objects.create(
            owner_app_label=request.POST.get("paperOwnerAppLabel"),
            owner_model_name=request.POST.get("paperOwnerModelName"),
            owner_fieldname=request.POST.get("paperOwnerFieldName"),
        )
        return self.success_response({
            "collection_id": collection.pk
        })


class DeleteCollectionView(ActionView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("paper_uploads.delete"):
            return self.error_response(_("Access denied"))
        return self.perform_action(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        content_type_id = request.POST.get("paperCollectionContentType")
        collection_cls = helpers.get_model_class(content_type_id, CollectionBase)
        collection_id = request.POST.get("pk")

        try:
            instance = helpers.get_instance(collection_cls, collection_id)
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


class UploadFileView(UploadFileViewBase):
    def handle(self, request, file: UploadedFile):
        content_type_id = request.POST.get("paperCollectionContentType")
        collection_cls = helpers.get_model_class(content_type_id, CollectionBase)
        collection_id = request.POST.get("collectionId")

        try:
            collection = helpers.get_instance(collection_cls, collection_id)
        except exceptions.InvalidObjectId:
            logger.exception("Error")
            return self.error_response(_("Invalid collection ID"))
        except ObjectDoesNotExist:
            logger.exception("Error")
            return self.error_response(_("Collection not found"))
        except MultipleObjectsReturned:
            logger.exception("Error")
            return self.error_response(_("Multiple objects returned"))

        try:
            order = max(0, int(request.POST.get("order")))
        except (TypeError, ValueError):
            order = 0

        # перебираем все подходящие классы элементов пока
        # не найдем тот, который будет успешно создан
        for item_type in collection.detect_item_type(file):  # noqa: F821
            item_type_field = collection_cls.item_types[item_type]
            instance = item_type_field.model(
                collection_content_type_id=content_type_id,
                collection_id=collection.pk,
                item_type=item_type,
                size=file.size,
                order=order
            )

            try:
                instance.attach_file(file)
            except exceptions.UnsupportedFileError:
                continue

            try:
                instance.full_clean()
                run_validators(file, item_type_field.validators)
            except Exception:
                instance.delete_file()
                raise

            break
        else:
            return self.error_response(_("Unsupported file: %s") % file.name)

        instance.save()
        return self.success_response({
            **instance.as_dict(),
        })


class DeleteFileView(DeleteFileViewBase):
    def handle(self, request):
        content_type_id = request.POST.get("paperCollectionContentType")
        collection_cls = helpers.get_model_class(content_type_id, CollectionBase)

        item_type = request.POST.get("itemType")
        for name, field in collection_cls.item_types.items():
            if item_type == name:
                model_class = field.model
                break
        else:
            return self.error_response(_("Invalid itemType"))

        item_id = request.POST.get("itemId")

        try:
            item = helpers.get_instance(model_class, item_id)
        except exceptions.InvalidObjectId:
            logger.exception("Error")
            return self.error_response(_("Invalid ID"))
        except ObjectDoesNotExist:
            # silently skip
            return self.success_response()
        except MultipleObjectsReturned:
            logger.exception("Error")
            return self.error_response(_("Multiple objects returned"))

        item.delete()
        return self.success_response()


class ChangeFileView(ChangeFileViewBase):
    template_name = "paper_uploads/dialogs/collection.html"

    def get_form_class(self):
        return import_string(self.instance.change_form_class)

    def get_instance(self, request, *args, **kwargs):
        content_type_id = self.request.GET.get("paperCollectionContentType")
        collection_cls = helpers.get_model_class(content_type_id, CollectionBase)

        item_type = self.request.GET.get("itemType")
        for name, field in collection_cls.item_types.items():
            if item_type == name:
                model_class = field.model
                break
        else:
            raise exceptions.AjaxFormError(_("Invalid itemType"))

        item_id = self.request.GET.get("itemId")

        try:
            return helpers.get_instance(model_class, item_id)
        except exceptions.InvalidObjectId:
            raise exceptions.AjaxFormError(_("Invalid ID"))
        except ObjectDoesNotExist:
            raise exceptions.AjaxFormError(_("Object not found"))
        except MultipleObjectsReturned:
            raise exceptions.AjaxFormError(_("Multiple objects returned"))


class SortItemsView(ActionView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("paper_uploads.change"):
            return self.error_response(_("Access denied"))

        return self.perform_action(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        content_type_id = request.POST.get("paperCollectionContentType")
        collection_cls = helpers.get_model_class(content_type_id, CollectionBase)
        collection_id = request.POST.get("collectionId")

        try:
            instance = helpers.get_instance(collection_cls, collection_id)
        except exceptions.InvalidObjectId:
            logger.exception("Error")
            return self.error_response(_("Invalid ID"))
        except ObjectDoesNotExist:
            logger.exception("Error")
            return self.error_response(_("Object not found"))
        except MultipleObjectsReturned:
            logger.exception("Error")
            return self.error_response(_("Multiple objects returned"))

        order_string = request.POST.get("orderList", "")
        try:
            item_ids = (int(pk) for pk in order_string.split(","))
        except ValueError:
            logger.exception("Error")
            return self.error_response(_("Invalid order value"))

        with transaction.atomic():
            for index, item_id in enumerate(item_ids):
                if item_id in set(instance.items.values_list("pk", flat=True)):  # noqa: F821
                    CollectionItemBase.objects.filter(pk=item_id).update(order=index)
                else:
                    CollectionItemBase.objects.filter(pk=item_id).update(
                        order=2 ** 32 - 1
                    )

        signals.collection_reordered.send(
            sender=collection_cls,
            instance=instance
        )
        return self.success_response({
            "orderMap": dict(instance.items.values_list("pk", "order"))  # noqa: F821
        })
