import os
from typing import Any, Generator, Tuple, Type, Union, cast

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from .. import exceptions, signals
from ..helpers import run_validators
from ..logging import logger
from ..models.collection import CollectionBase, CollectionFileItemBase, CollectionItemBase
from ..models.fields.collection import CollectionItem
from ..models.mixins import EditableResourceMixin
from . import helpers
from .base import AjaxView, ChangeFileViewBase, DeleteFileViewBase, UploadFileViewBase


class CreateCollectionView(AjaxView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.has_perm("paper_uploads.upload"):
            return self.error_response(_("Access denied"))
        return self.wrap(self.handle)()

    def get_collection_model(self) -> Type[CollectionBase]:
        content_type_id = self.request.POST.get("paperCollectionContentType")
        return helpers.get_model_class(content_type_id, CollectionBase)

    def get_instance(self) -> CollectionBase:
        collection_cls = self.get_collection_model()
        return collection_cls(
            owner_app_label=self.request.POST.get("paperOwnerAppLabel"),
            owner_model_name=self.request.POST.get("paperOwnerModelName"),
            owner_fieldname=self.request.POST.get("paperOwnerFieldName"),
        )

    def handle(self) -> HttpResponse:
        instance = self.get_instance()
        instance.save()
        return self.success(instance)

    def success(self, instance: CollectionBase) -> HttpResponse:
        return self.success_response({
            "collection_id": instance.pk
        })


class DeleteCollectionView(AjaxView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.has_perm("paper_uploads.delete"):
            return self.error_response(_("Access denied"))
        return self.wrap(self.handle)()

    def get_collection_model(self) -> Type[CollectionBase]:
        content_type_id = self.request.POST.get("paperCollectionContentType")
        return helpers.get_model_class(content_type_id, CollectionBase)

    def get_collection_id(self) -> Any:
        return self.request.POST.get("collectionId")

    def get_instance(self) -> CollectionBase:
        collection_cls = self.get_collection_model()
        collection_id = self.get_collection_id()
        return cast(CollectionBase, helpers.get_instance(collection_cls, collection_id))

    def handle(self) -> HttpResponse:
        collection = self.get_instance()
        collection.delete()
        return self.success()

    def success(self) -> HttpResponse:
        return self.success_response()


class UploadFileView(UploadFileViewBase):
    def get_collection_model(self) -> Type[CollectionBase]:
        content_type_id = self.request.POST.get("paperCollectionContentType")
        return helpers.get_model_class(content_type_id, CollectionBase)

    def get_collection_id(self) -> Any:
        return self.request.POST.get("collectionId")

    def get_collection_instance(self) -> CollectionBase:
        collection_cls = self.get_collection_model()
        collection_id = self.get_collection_id()
        return cast(CollectionBase, helpers.get_instance(collection_cls, collection_id))

    def get_instance(self, item_type: str, **kwargs) -> CollectionItemBase:
        collection_cls = self.get_collection_model()
        item_model = collection_cls.get_item_model(item_type)
        return item_model(
            type=item_type,
            **kwargs
        )

    def get_order(self) -> int:
        order = self.request.POST.get("order")

        try:
            order = max(0, int(order))
        except (TypeError, ValueError):
            order = None

        return order

    def get_accepted_item_types(
        self,
        collection: Union[CollectionBase, Type[CollectionBase]],
        file: UploadedFile
    ) -> Generator[Tuple[str, CollectionItem], Any, None]:
        for item_type, field in collection.item_types.items():
            if issubclass(field.model, CollectionFileItemBase) and field.model.accept(file):
                yield item_type, field

    def handle(self, file: UploadedFile) -> HttpResponse:
        collection = self.get_collection_instance()

        # перебираем все подходящие классы элементов пока
        # не найдем тот, который будет успешно создан
        for item_type, item_type_field in self.get_accepted_item_types(collection, file):
            item = self.get_instance(
                collection=collection,
                item_type=item_type,
                size=file.size,
                order=self.get_order()
            )

            try:
                item.attach(file)
            except exceptions.UnsupportedResource:
                continue

            try:
                item.full_clean()
                run_validators(file, item_type_field.validators)
            except Exception:
                item.delete_file()
                raise

            break
        else:
            filename = os.path.basename(file.name)
            return self.error_response(_("Unsupported file: %s") % filename)

        item.save()

        if not file.closed:
            file.close()

        return self.success(item)

    def success(self, instance: CollectionItemBase) -> HttpResponse:
        return self.success_response(instance.as_dict())


class DeleteFileView(DeleteFileViewBase):
    def get_collection_model(self) -> Type[CollectionBase]:
        content_type_id = self.request.POST.get("paperCollectionContentType")
        return helpers.get_model_class(content_type_id, CollectionBase)

    def get_item_type(self) -> str:
        return self.request.POST.get("itemType")

    def get_item_id(self) -> Any:
        return self.request.POST.get("itemId")

    def get_instance(self) -> CollectionItemBase:
        collection_cls = self.get_collection_model()
        item_type = self.get_item_type()
        item_model = collection_cls.get_item_model(item_type)
        item_id = self.get_item_id()
        return cast(CollectionItemBase, helpers.get_instance(item_model, item_id))

    def handle(self) -> HttpResponse:
        try:
            item = self.get_instance()
        except ObjectDoesNotExist:
            # silently skip
            pass
        else:
            item.delete()

        return self.success()

    def success(self) -> HttpResponse:
        return self.success_response()


class ChangeFileView(ChangeFileViewBase):
    template_name = "paper_uploads/dialogs/collection.html"

    def get_collection_model(self) -> Type[CollectionBase]:
        content_type_id = self.request.GET.get("paperCollectionContentType")
        return helpers.get_model_class(content_type_id, CollectionBase)

    def get_item_type(self) -> str:
        return self.request.GET.get("itemType")

    def get_item_id(self) -> Any:
        return self.request.GET.get("itemId")

    def get_instance(self) -> CollectionItemBase:
        collection_cls = self.get_collection_model()
        item_id = self.get_item_id()
        item_type = self.get_item_type()
        item_model = collection_cls.get_item_model(item_type)
        return cast(CollectionItemBase, helpers.get_instance(item_model, item_id))

    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class

        collection_cls = self.get_collection_model()
        item_type = self.get_item_type()
        item_model = collection_cls.get_item_model(item_type)
        if issubclass(item_model, EditableResourceMixin):
            return import_string(item_model.change_form_class)


class SortItemsView(AjaxView):
    http_method_names = ["post"]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request: WSGIRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.has_perm("paper_uploads.change"):
            return self.error_response(_("Access denied"))
        return self.wrap(self.handle)()

    def get_collection_model(self) -> Type[CollectionBase]:
        content_type_id = self.request.POST.get("paperCollectionContentType")
        return helpers.get_model_class(content_type_id, CollectionBase)

    def get_collection_id(self) -> Any:
        return self.request.POST.get("collectionId")

    def handle(self) -> HttpResponse:
        collection_cls = self.get_collection_model()
        collection_id = self.get_collection_id()
        collection_content_type = ContentType.objects.get_for_model(collection_cls, for_concrete_model=False)
        collection = helpers.get_instance(collection_cls, collection_id)

        # Получение списка ID элементов в том порядке, в котором они должны быть расположены
        order_string = self.request.POST.get("orderList", "")
        ordered_item_ids = (item.strip() for item in order_string.split(","))
        ordered_item_ids = tuple(pk for pk in ordered_item_ids if pk)

        # Список ID и сортировки для существующих элементов коллекции
        existing_item_ids = {
            str(pk): order
            for pk, order in CollectionItemBase._base_manager.filter(
                collection_content_type=collection_content_type,
                collection_id=collection_id
            ).values_list("pk", "order")
        }

        with transaction.atomic():
            for index, item_id in enumerate(ordered_item_ids):
                if item_id in existing_item_ids:
                    # обновляем только те значения сортировки, которые изменились
                    if existing_item_ids[item_id] != index:
                        CollectionItemBase._base_manager.filter(
                            pk=item_id
                        ).update(
                            order=index
                        )
                else:
                    logger.warning(
                        "Item #{} not found in collection #{}".format(item_id, collection_id)
                    )

        signals.collection_reordered.send(
            sender=collection_cls,
            instance=collection
        )

        return self.success_response({
            "orderMap": dict(CollectionItemBase._base_manager.filter(
                collection_content_type=collection_content_type,
                collection_id=collection_id
            ).values_list("pk", "order"))
        })
