import sys
from typing import Type, cast

from anytree import LevelOrderIter
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from ... import exceptions, helpers
from ...models.base import FileFieldResource, FileResource, VersatileImageResourceMixin
from ...models.collection import Collection, CollectionItemBase
from ...models.mixins import BacklinkModelMixin


class Command(BaseCommand):
    help = """
    Проверка целостности экземпляров файловых моделей.
    """
    options = None
    verbosity = None
    database = DEFAULT_DB_ALIAS

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates the database to use. Defaults to the 'default' database.",
        )
        parser.add_argument(
            "-o", "--check-ownership",
            action="store_true",
            default=False,
            help="Check `owner_XXX` fields.",
        )
        parser.add_argument(
            "-f", "--check-files-exist",
            action="store_true",
            default=False,
            help="Check file existence.",
        )
        parser.add_argument(
            "-c", "--check-content-types",
            action="store_true",
            default=False,
            help="Check collection ContentType.",
        )
        parser.add_argument(
            "-t", "--check-item-types",
            action="store_true",
            default=False,
            help="Check item `type` values.",
        )

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]
        self.run_steps()

    def run_steps(self):
        check_ownership = self.options["check_ownership"]
        check_files_exist = self.options["check_files_exist"]
        check_content_types = self.options["check_content_types"]
        check_item_types = self.options["check_item_types"]

        check_all = not any([
            check_ownership,
            check_files_exist,
            check_content_types,
            check_item_types,
        ])

        if check_all or check_ownership:
            self.check_ownership()

        if check_all or check_files_exist:
            self.check_files_exist()

        if check_all or check_content_types:
            self.check_content_types()

        if check_all or check_item_types:
            self.check_item_types()

    def check_ownership(self):
        """
        Проверяет, что ресурсы и коллекции
        *) имеют значения owner_app_label и owner_model_name, ссылающиеся на существующую модель
        *) имя поля, указанное в owner_fieldname существует в классе модели владельца
        """
        for root in helpers.get_resource_model_trees():
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model
                self._check_model_ownership(model)

        for root in helpers.get_collection_trees(include_proxy=True):
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model

                if model is Collection:
                    continue

                self._check_model_ownership(model)

    def _check_model_ownership(self, model: Type[BacklinkModelMixin]):
        if not issubclass(model, BacklinkModelMixin):
            return

        queryset = model.objects.using(self.database).only(
            "pk",
            "owner_app_label",
            "owner_model_name",
            "owner_fieldname"
        )
        for instance in queryset.iterator():
            owner_model = instance.get_owner_model()
            if owner_model is None:
                print(
                    "\033[31mERROR\033[0m: "
                    "\033[92m{}.{}\033[0m #{} has an invalid owner reference: "
                    "\033[91m{}.{}\033[0m".format(
                        type(instance)._meta.app_label,
                        type(instance).__name__,
                        instance.pk,
                        instance.owner_app_label,
                        instance.owner_model_name,
                    ),
                    file=sys.stderr
                )
                sys.stderr.flush()
                continue

            if not instance.owner_fieldname:
                print(
                    "\033[31mERROR\033[0m: "
                    "\033[92m{}.{}\033[0m #{} has an empty \033[92mowner_fieldname\033[0m field".format(
                        type(instance)._meta.app_label,
                        type(instance).__name__,
                        instance.pk,
                    ),
                    file=sys.stderr
                )
                sys.stderr.flush()
                continue

            try:
                owner_model._meta.get_field(instance.owner_fieldname)
            except FieldDoesNotExist:
                print(
                    "\033[31mERROR\033[0m: "
                    "\033[92m{}.{}\033[0m #{} references a field name that does not exist: \033[91m{}\033[0m".format(
                        type(instance)._meta.app_label,
                        type(instance).__name__,
                        instance.pk,
                        instance.owner_fieldname
                    ),
                    file=sys.stderr
                )
                sys.stderr.flush()
                continue

    def check_content_types(self):
        """
        Проверяет, что для коллекций
        *) существует модель, заданная через ContentType.
        """
        for root in helpers.get_collection_trees():
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model
                self._check_content_types(model)

    def _check_content_types(self, model: Type[Collection]):
        queryset = model.objects.using(self.database)
        for instance in queryset.iterator():
            content_type_id = instance.collection_content_type_id
            content_type = ContentType.objects.get_for_id(content_type_id)
            model_class = content_type.model_class()
            if model_class is None:
                print(
                    "\033[31mERROR\033[0m: "
                    "Collection #{} refers to a model \033[92m{}.{}\033[0m that does not exist.".format(
                        instance.pk,
                        content_type.app_label,
                        content_type.model
                    ),
                    file=sys.stderr
                )
                sys.stderr.flush()

    def check_files_exist(self):
        """
        Проверяет, что экземпляры файловых ресурсов (UploadedFile, UploadedImage и т.п.)
        и файловых элементов коллекций ссылаются на существующие файлы.

        P.S.: Не проверяет существование вариаций изображений!
        """
        for root in helpers.get_resource_model_trees():
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model
                self._check_files_exist(model)

    def _check_files_exist(self, model: Type[FileResource]):
        if not issubclass(model, FileResource):
            return

        queryset = model.objects.using(self.database)
        query_fields = []

        if issubclass(model, FileFieldResource):
            model = cast(Type[FileFieldResource], model)
            file_field = model.get_file_field()
            query_fields.append(file_field.name)

        if issubclass(model, VersatileImageResourceMixin):
            # Для инициализации экземпляров VersatileImageResourceMixin нужны
            # дополнительные поля - для создания полей вариаций.
            if issubclass(model, BacklinkModelMixin):
                query_fields.extend([
                    "owner_app_label",
                    "owner_model_name",
                    "owner_fieldname"
                ])

            if issubclass(model, CollectionItemBase):
                query_fields.extend([
                    "collection_content_type_id",
                    "polymorphic_ctype_id",
                    "type",
                ])

        queryset = queryset.only(*query_fields)

        for instance in queryset.iterator():
            if not instance.file_exists():
                print(
                    "\033[31mERROR\033[0m: "
                    "\033[92m{}.{}\033[0m #{} references a file that does not exist".format(
                        type(instance)._meta.app_label,
                        type(instance).__name__,
                        instance.pk
                    ),
                    file=sys.stderr
                )
                sys.stderr.flush()

    def check_item_types(self):
        """
        Проверяет, что элементы коллекций
        *) имеют значение type, которое присутствует в коллекции
        *) имеют класс, соответствующий модели, указанной для данного type
        """
        queryset = CollectionItemBase.objects.using(self.database)
        for item in queryset.iterator():
            try:
                collection_cls = item.get_collection_class()
            except exceptions.CollectionModelNotFoundError:
                continue

            if item.type not in collection_cls.item_types:
                print(
                    "\033[31mERROR\033[0m: "
                    "\033[92m{}.{}\033[0m #{} has a type value that has not been declared "
                    "in the \033[92m{}.{}\033[0m: \033[91m{}\033[0m".format(
                        type(item)._meta.app_label,
                        type(item).__name__,
                        item.pk,
                        collection_cls._meta.app_label,
                        collection_cls.__name__,
                        item.type,
                    ),
                    file=sys.stderr
                )
                sys.stderr.flush()
                continue

            item_model = collection_cls.get_item_model(item.type)
            if not issubclass(type(item), item_model):
                print(
                    "\033[31mERROR\033[0m: "
                    "\033[92m{}.{}\033[0m #{} has a class type different from that "
                    "specified in the \033[92m{}.{}\033[0m as \033[92m{}\033[0m type: "
                    "\033[91m{}.{}\033[0m".format(
                        type(item)._meta.app_label,
                        type(item).__name__,
                        item.pk,
                        collection_cls._meta.app_label,
                        collection_cls.__name__,
                        item.type,
                        item_model._meta.app_label,
                        item_model.__name__,
                    ),
                    file=sys.stderr
                )
                sys.stderr.flush()
                continue
