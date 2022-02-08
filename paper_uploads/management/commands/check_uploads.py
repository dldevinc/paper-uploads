from typing import Type

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from ... import helpers
from ...models.base import FileResource, VersatileImageResourceMixin
from ...models.collection import CollectionBase, CollectionItemBase
from ...models.mixins import BacklinkModelMixin


class Command(BaseCommand):
    help = """
    Проверка экземпляров файловых моделей.
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
            "-f", "--check-files",
            action="store_true",
            default=False,
            help="Check file existence.",
        )
        parser.add_argument(
            "-t", "--check-item-types",
            action="store_true",
            default=False,
            help="Check item `type` values.",
        )
        parser.add_argument(
            "-r", "--fix-missing-variations",
            action="store_true",
            default=False,
            help="Recreate all missing variation files from a source image.",
        )

    def _check_model_owners(self, model: Type[BacklinkModelMixin]):
        for instance in model.objects.using(self.database).iterator():
            invalid = False
            message = "The following errors were found in '{}.{}' (ID: {instance.pk}):".format(
                type(instance)._meta.app_label,
                type(instance).__name__,
                instance=instance,
            )

            owner_model = instance.get_owner_model()
            if owner_model is None:
                invalid = True
                message += "\n  Owner model '{}.{}' doesn't exists".format(
                    instance.owner_app_label,
                    instance.owner_model_name,
                )
            else:
                owner_field = instance.get_owner_field()
                if owner_field is None:
                    invalid = True
                    message += "\n  Owner model '{}.{}' has no field named '{}'".format(
                        instance.owner_app_label,
                        instance.owner_model_name,
                        instance.owner_fieldname,
                    )
                else:
                    try:
                        owner_model._base_manager.get(
                            (instance.owner_fieldname, instance.pk)
                        )
                    except owner_model.DoesNotExist:
                        invalid = True
                        message += "\n  Owner instance '{}.{}' not found".format(
                            instance.owner_app_label,
                            instance.owner_model_name,
                        )
                    except owner_model.MultipleObjectsReturned:
                        invalid = True
                        message += "\n  Multiple owners"

            if invalid:
                self.stdout.write(self.style.ERROR(message))

    def check_owners(self):
        """
        Проверяет, что ресурсы и коллекции
        *) имеют значения owner_app_label и owner_model_name, ссылающиеся на существующую модель
        *) имеют в поле owner_fieldname название поля, объявленного в модели-владельце
        *) имеют существующий экземпляр модели-владельца, ссылающийся на данный файл / коллекцию,
           и этот экземпляр единственный
        """
        if self.verbosity >= 2:
            self.stdout.write(self.style.SUCCESS("Checking resource ownership..."))

        for node in helpers.get_resource_model_trees(include_proxy=False):
            model = node.model

            if not issubclass(model, BacklinkModelMixin):
                continue

            self._check_model_owners(model)

        for model in apps.get_models():
            if not issubclass(model, CollectionBase):
                continue

            if model._meta.proxy:
                continue

            self._check_model_owners(model)

    def _check_file_existence(self, model: Type[FileResource]):
        for instance in model.objects.using(self.database).iterator():
            invalid = False
            message = "The following errors were found in '{}.{}' (ID: {instance.pk}):".format(
                type(instance)._meta.app_label,
                type(instance).__name__,
                instance=instance
            )

            if not instance.file_exists():
                invalid = True
                message += "\n  File missing: {}".format(instance.name)

            if invalid:
                self.stdout.write(self.style.ERROR(message))

    def check_file_existence(self):
        """
        Проверяет, что экземпляры загруженных файлов (UploadedFile, UploadedImage и т.п.)
        и элементов коллекций ссылаются на существующие файлы.

        P.S.: Не проверяет существование вариаций изображений!
        """
        if self.verbosity >= 2:
            self.stdout.write(self.style.SUCCESS("Checking file existence..."))

        for node in helpers.get_resource_model_trees(include_proxy=False):
            model = node.model

            if not issubclass(model, FileResource):
                continue

            self._check_file_existence(model)

    def check_item_types(self):
        """
        Проверяет, что элементы коллекций
        *) имеют значение type, которое присутствует в коллекции
        *) имеют класс, соответствующий модели, указанной для данного type
        """
        if self.verbosity >= 2:
            self.stdout.write(self.style.SUCCESS("Checking item type values..."))

        for item in CollectionItemBase.objects.using(self.database).iterator():
            invalid = False
            message = "The following errors were found in '{}.{}' (ID: {item.pk}):".format(
                type(item)._meta.app_label,
                type(item).__name__,
                item=item
            )

            collection_cls = item.get_collection_class()
            if item.type not in collection_cls.item_types:
                invalid = True
                message += "\n  Item type '{}' is not defined in collection '{}.{}' (ID: {})".format(
                    item.type,
                    collection_cls._meta.app_label,
                    collection_cls.__name__,
                    item.collection_id,
                )
            else:
                item_model = collection_cls.get_item_model(item.type)
                if item_model is not type(item):
                    invalid = True
                    message += "\n  Item class '{}.{}' differs from '{}.{}' defined for '{}' item type".format(
                        item._meta.app_label,
                        item.__name__,
                        item_model._meta.app_label,
                        item_model.__name__,
                        item.type
                    )

            if invalid:
                self.stdout.write(self.style.ERROR(message))

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]

        check_ownership = options["check_ownership"]
        check_files = options["check_files"]
        check_item_types = options["check_item_types"]

        check_all = not any([
            check_ownership,
            check_files,
            check_item_types,
        ])

        if check_all or check_ownership:
            self.check_owners()

        if check_all or check_files:
            self.check_file_existence()

        if check_all or check_item_types:
            self.check_item_types()
