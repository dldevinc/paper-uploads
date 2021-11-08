from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from ...models.base import FileResource, VersatileImageResourceMixin
from ...models.collection import Collection, CollectionItemBase
from ...models.mixins import BacklinkModelMixin


class Command(BaseCommand):
    help = """
    Проверка целостности экземпляров файловых моделей.
    
    Если указан параметр `--fix-missing`, недостающие файлы вариаций
    создаются из исходного изображения.
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
            "--fix-missing",
            action="store_true",
            default=False,
            help="Recreate all missing variation files from a source.",
        )

    def check_exists(self):
        """
        Проверяет, что экземпляры загруженных файлов (UploadedFile, UploadedImage и т.п.)
        и элементов коллекций ссылаются на существующие файлы.
        """
        for model in apps.get_models():
            if not issubclass(model, FileResource):
                continue

            total = model._base_manager.using(self.database).count()
            if not total:
                continue

            queryset = model._base_manager.using(self.database)
            for index, instance in enumerate(queryset.iterator(), start=1):
                if self.verbosity >= 2:
                    self.stdout.write("\r" + (" " * 80), ending="\r")

                invalid = False
                message = "The following errors were found in '{}.{}' #{instance.pk}:".format(
                    model._meta.app_label,
                    model.__name__,
                    instance=instance
                )

                if not instance.file_exists():
                    invalid = True
                    message += "\n  Not found source file"

                if invalid:
                    self.stdout.write(self.style.ERROR(message))

                if self.verbosity >= 2:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Check file existence of '{}.{}' ({}/{}) ...\r".format(
                                model._meta.app_label,
                                model.__name__,
                                index,
                                total,
                            )
                        ),
                        ending="",
                    )

            if self.verbosity >= 2:
                self.stdout.write("")

    def check_variations(self):
        """
        Проверяет, что для всех вариаций всех экземпляров загруженных изображений
        существуют соответсвующие файлы.
        """
        for model in apps.get_models():
            if not issubclass(model, VersatileImageResourceMixin):
                continue

            total = model._base_manager.using(self.database).count()
            if not total:
                continue

            for index, instance in enumerate(
                model._base_manager.using(self.database).iterator(), start=1
            ):
                if self.verbosity >= 2:
                    self.stdout.write("\r" + (" " * 80), ending="\r")

                invalid = False
                message = "The following errors were found in '{}.{}' #{instance.pk}:".format(
                    model._meta.app_label,
                    model.__name__,
                    instance=instance
                )

                missed_variations = []
                for vname, vfile in instance.variation_files():
                    if vfile is not None and not vfile.exists():
                        missed_variations.append(vname)

                if missed_variations:
                    invalid = True
                    recreatable = self.options["fix_missing"] and instance.file_exists()
                    for vname in missed_variations:
                        message += "\n  Not found variation '{}'".format(vname)
                        if recreatable:
                            message += self.style.SUCCESS(" (recreated)")

                    if recreatable:
                        instance.recut(names=missed_variations)

                if invalid:
                    self.stdout.write(self.style.ERROR(message))

                if self.verbosity >= 2:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Check variation existence of '{}.{}' ({}/{}) ...\r".format(
                                model._meta.app_label,
                                model.__name__,
                                index,
                                total,
                            )
                        ),
                        ending="",
                    )

            if self.verbosity >= 2:
                self.stdout.write("")

    def check_owners(self):
        """
        Проверяет, что загруженные объекты (UploadedFile, UploadedImage и т.п.) и коллекции
        *) имеют значения owner_app_label и owner_model_name, ссылающиеся на существующую модель
        *) имеют в поле owner_fieldname название поля, объявленного в модели-владельце
        *) имеют существующий экземпляр модели-владельца, ссылающийся на данный файл / коллекцию,
           и этот экземпляр единственный
        """
        for model in apps.get_models():
            if not issubclass(model, BacklinkModelMixin):
                continue

            if model._meta.proxy:
                continue

            total = model._base_manager.using(self.database).count()
            if not total:
                continue

            for index, instance in enumerate(
                model._base_manager.using(self.database).iterator(), start=1
            ):
                if self.verbosity >= 2:
                    self.stdout.write("\r" + (" " * 80), ending="\r")

                real_model = model
                if isinstance(instance, Collection):
                    real_model = instance.collection_content_type.model_class()

                invalid = False
                message = "The following errors were found in '{}.{}' #{instance.pk}:".format(
                    real_model._meta.app_label,
                    real_model.__name__,
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

                if self.verbosity >= 2:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Check owner of '{}.{}' ({}/{}) ...\r".format(
                                model._meta.app_label,
                                model.__name__,
                                index,
                                total,
                            )
                        ),
                        ending="",
                    )

            if self.verbosity >= 2:
                self.stdout.write("")

    def check_item_types(self):
        """
        Проверяет, что элементы коллекций
        *) имеют значение item_type, которое присутствует в коллекции
        *) имеют класс, соответствующий модели, указанной для данного item_type
        """
        total = CollectionItemBase.objects.using(self.database).count()
        for index, item in enumerate(
            CollectionItemBase.objects.using(self.database).iterator(),
            start=1
        ):
            if self.verbosity >= 2:
                self.stdout.write("\r" + (" " * 80), ending="\r")

            invalid = False
            message = "The following errors were found in '{}.{}' #{item.pk}:".format(
                item._meta.app_label,
                type(item).__name__,
                item=item
            )

            collection_cls = item.get_collection_class()
            if item.item_type not in collection_cls.item_types:
                invalid = True
                message += "\n  Item type '{}' is not defined in collection '{}.{}' #{}".format(
                    item.item_type,
                    collection_cls._meta.app_label,
                    collection_cls.__name__,
                    item.collection_id,
                )
            else:
                item_model = collection_cls.item_types[item.item_type].model
                if item_model is not type(item):
                    invalid = True
                    message += "\n  Item class '{}.{}' differs from '{}.{}' defined for '{}' item type".format(
                        item._meta.app_label,
                        item.__name__,
                        item_model._meta.app_label,
                        item_model.__name__,
                        item.item_type
                    )

            if invalid:
                self.stdout.write(self.style.ERROR(message))

            if self.verbosity >= 2:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Check item_type of collection items ({}/{}) ...\r".format(
                            index, total
                        )
                    ),
                    ending="",
                )

        if self.verbosity >= 2:
            self.stdout.write("")

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]

        self.check_item_types()
        self.check_owners()
        self.check_exists()
        self.check_variations()
