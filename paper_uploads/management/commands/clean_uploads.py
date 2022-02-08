import datetime
from collections import defaultdict
from datetime import timedelta
from typing import Type

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from django.utils.timezone import now

from ... import helpers
from ...models.base import FileResource
from ...models.collection import CollectionBase
from ...models.mixins import BacklinkModelMixin


class Command(BaseCommand):
    help = """
    Поиск и удаление экземпляров файловых моделей с утерянными файлами.
    Также удаляются экземпляры файловых моделей, на которые нет ссылок.
    
    Создание экземпляра файловой модели и загрузка в неё файла - это  две отдельные 
    операции. Между ними может пройти какое-то время, особенно при использовании 
    django-rq. Для того, чтобы сохранить экземпляры, в которые ещё не загрузились файлы,
    эта команда пропускает те экземпляры, которые созданы недавно.  Временной интервал 
    задаётся через параметр `--threshold` и по умолчанию составляет 24 часа.
    """
    verbosity = None
    database = DEFAULT_DB_ALIAS
    interactive = True

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
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=24 * 3600,
            help="Minimum instance age in seconds to look for",
        )

    def _get_start_time(self) -> datetime.datetime:
        return now() - timedelta(seconds=self.options["threshold"])

    def _clean_objects_with_invalid_ownership(self, model: Type[BacklinkModelMixin]):
        grouped_invalid_objects = defaultdict(list)

        queryset = model.objects.using(self.database).filter(created_at__lte=self._get_start_time())
        for instance in queryset.iterator():
            owner_model = instance.get_owner_model()
            if owner_model is None:
                model = type(instance)
                grouped_invalid_objects[model].append(instance)
            else:
                owner_field = instance.get_owner_field()
                if owner_field is None:
                    model = type(instance)
                    grouped_invalid_objects[model].append(instance)
                else:
                    try:
                        owner_model._base_manager.using(self.database).get(
                            (instance.owner_fieldname, instance.pk)
                        )
                    except owner_model.DoesNotExist:
                        model = type(instance)
                        grouped_invalid_objects[model].append(instance)

        if not grouped_invalid_objects:
            return

        if self.interactive:
            for actual_model, instances in grouped_invalid_objects.items():
                while True:
                    print("-" * 64)
                    answer = input(
                        "Found \033[92m%d '%s.%s'\033[0m objects with invalid ownership.\n"
                        "IDs: %s\n"
                        "What would you like to do with them?\n"
                        "(p)rint / (k)eep / (d)elete [default=keep]? "
                        % (
                            len(instances),
                            actual_model._meta.app_label,
                            actual_model.__name__,
                            ", ".join(map(str, [obj.pk for obj in instances])),
                        )
                    )
                    answer = answer.lower() or "k"
                    if answer in {"p", "print"}:
                        self.stdout.write("\n")

                        sorted_objects = sorted(instances, key=lambda obj: obj.pk)
                        for index, obj in enumerate(sorted_objects, start=1):
                            prefix = "{})".format(index)
                            self.stdout.write(
                                "{:<3} \033[92m{}.{}\033[0m (ID: {})\n"
                                "    File: {}".format(
                                    prefix,
                                    actual_model._meta.app_label,
                                    actual_model.__name__,
                                    obj.pk,
                                    obj.name,
                                )
                            )
                        self.stdout.write("\n")
                    elif answer in {"k", "keep"}:
                        break
                    elif answer in {"d", "delete"}:
                        model.objects.using(self.database).filter(
                            pk__in=[obj.pk for obj in instances]
                        ).delete()
                        break
        else:
            for actual_model, instances in grouped_invalid_objects.items():
                model.objects.using(self.database).filter(
                    pk__in=[obj.pk for obj in instances]
                ).delete()

    def clean_objects_with_invalid_ownership(self):
        if self.verbosity >= 2:
            self.stdout.write(self.style.SUCCESS("Checking resource ownership..."))

        for node in helpers.get_resource_model_trees(include_proxy=False):
            model = node.model

            if not issubclass(model, BacklinkModelMixin):
                continue

            self._clean_objects_with_invalid_ownership(model)

        for model in apps.get_models():
            if not issubclass(model, CollectionBase):
                continue

            if model._meta.proxy:
                continue

            self._clean_objects_with_invalid_ownership(model)

    def _clean_objects_with_missing_files(self, model: Type[FileResource]):
        """
        Поиск экземпляров с утерянными файлами
        """
        grouped_invalid_objects = defaultdict(list)

        queryset = model.objects.using(self.database).filter(created_at__lte=self._get_start_time())
        for instance in queryset.iterator():
            if not instance.file_exists():
                model = type(instance)
                grouped_invalid_objects[model].append(instance)

        if not grouped_invalid_objects:
            return

        if self.interactive:
            for actual_model, instances in grouped_invalid_objects.items():
                while True:
                    print("-" * 64)
                    answer = input(
                        "Found \033[92m%d '%s.%s'\033[0m objects that refers to a file that does not exist.\n"
                        "IDs: %s\n"
                        "What would you like to do with them?\n"
                        "(p)rint / (k)eep / (d)elete [default=keep]? "
                        % (
                            len(instances),
                            actual_model._meta.app_label,
                            actual_model.__name__,
                            ", ".join(map(str, [obj.pk for obj in instances])),
                        )
                    )
                    answer = answer.lower() or "k"
                    if answer in {"p", "print"}:
                        self.stdout.write("\n")

                        sorted_objects = sorted(instances, key=lambda obj: obj.pk)
                        for index, obj in enumerate(sorted_objects, start=1):
                            prefix = "{})".format(index)
                            self.stdout.write(
                                "{:<3} \033[92m{}.{}\033[0m (ID: {})\n"
                                "    File: {}".format(
                                    prefix,
                                    actual_model._meta.app_label,
                                    actual_model.__name__,
                                    obj.pk,
                                    obj.name,
                                )
                            )
                        self.stdout.write("\n")
                    elif answer in {"k", "keep"}:
                        break
                    elif answer in {"d", "delete"}:
                        model.objects.using(self.database).filter(
                            pk__in=[obj.pk for obj in instances]
                        ).delete()
                        break
        else:
            for actual_model, instances in grouped_invalid_objects.items():
                model.objects.using(self.database).filter(
                    pk__in=[obj.pk for obj in instances]
                ).delete()

    def clean_objects_with_missing_files(self):
        if self.verbosity >= 2:
            self.stdout.write(self.style.SUCCESS("Checking file existence..."))

        for node in helpers.get_resource_model_trees(include_proxy=False):
            model = node.model

            if not issubclass(model, FileResource):
                continue

            self._clean_objects_with_missing_files(model)

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]
        self.interactive = options["interactive"]

        check_ownership = options["check_ownership"]
        check_files = options["check_files"]

        check_all = not any([
            check_ownership,
            check_files,
        ])

        if check_all or check_ownership:
            self.clean_objects_with_invalid_ownership()

        if check_all or check_files:
            self.clean_objects_with_missing_files()
