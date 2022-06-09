from datetime import timedelta
from enum import Enum, auto
from typing import Type

from anytree import LevelOrderIter
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS, transaction
from django.utils.timezone import now

from ... import helpers
from ...models.base import FileResource
from ...models.collection import Collection, CollectionBase, CollectionItemBase
from ...models.mixins import BacklinkModelMixin
from ..prompt import prompt_action


class Step(Enum):
    CHECK_CONTENT_TYPES = auto()
    CHECK_OWNERSHIP = auto()
    CHECK_FILES = auto()
    END = auto()


class ExitException(Exception):
    pass


class Command(BaseCommand):
    help = """
    Находит некорректные экземпляры файловых моделей и предлагает их удалить.
    
    Некорректными считаются экземпляры, у которых утерян загруженный файл,
    а также экземпляры, на которые нет ссылки.
    
    Создание экземпляра файловой модели и загрузка в неё файла - это  две отдельные 
    операции. Между ними может пройти какое-то время, особенно при использовании 
    django-rq. Для того, чтобы сохранить экземпляры, в которые ещё не загрузились файлы,
    эта команда пропускает те экземпляры, которые созданы недавно.  Временной интервал 
    задаётся через параметр `--threshold` и по умолчанию составляет 24 часа.
    """
    verbosity = None
    database = DEFAULT_DB_ALIAS

    _step = Step.CHECK_CONTENT_TYPES
    _check_content_types = False
    _check_ownership = False
    _check_file_existence = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates the database to use. Defaults to the 'default' database.",
        )
        parser.add_argument(
            "-c", "--check-content-types",
            action="store_true",
            default=False,
            help="Check collection ContentType.",
        )
        parser.add_argument(
            "-o", "--check-ownership",
            action="store_true",
            default=False,
            help="Check `owner_XXX` fields.",
        )
        parser.add_argument(
            "-f", "--check-file-existence",
            action="store_true",
            default=False,
            help="Check file existence.",
        )
        parser.add_argument(
            "--min-age",
            type=int,
            default=24 * 3600,
            help="Minimum instance age in seconds to look for",
        )

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]

        check_content_types = self.options["check_content_types"]
        check_ownership = self.options["check_ownership"]
        check_file_existence = self.options["check_file_existence"]
        check_all = not any([
            check_content_types,
            check_ownership,
            check_file_existence,
        ])

        self._check_content_types = check_content_types or check_all
        self._check_ownership = check_ownership or check_all
        self._check_file_existence = check_file_existence or check_all

        try:
            self.loop()
        except ExitException:
            return

    def loop(self):
        while True:
            if self._step is Step.CHECK_CONTENT_TYPES:
                self.clean_invalid_content_types()
            elif self._step is Step.CHECK_OWNERSHIP:
                self.clean_invalid_ownership()
            elif self._step is Step.CHECK_FILES:
                self.clean_file_existence()
            else:
                return

    def clean_invalid_content_types(self):
        """
        Удаление коллекций, у которых:
        *) отсутствует модель, заданная через ContentType.
        """
        if not self._check_content_types:
            self._step = Step.CHECK_OWNERSHIP
            return

        for root in helpers.get_collection_trees():
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model
                self._clean_invalid_content_types(model)

        self._step = Step.CHECK_OWNERSHIP

    def _clean_invalid_content_types(self, model: Type[Collection]):
        created_before = now() - timedelta(seconds=self.options["min_age"])
        queryset = model.objects.using(self.database).filter(
            created_at__lte=created_before
        )

        objects = set()
        for instance in queryset.iterator():
            content_type_id = instance.collection_content_type_id
            content_type = ContentType.objects.get_for_id(content_type_id)
            model_class = content_type.model_class()
            if model_class is None:
                objects.add(instance)

        if not objects:
            return

        count = len(objects)
        while True:
            action = prompt_action(
                message=(
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m instance "
                    "that has an invalid content type.\n"
                    "What would you like to do with it?"
                    if count == 1 else
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m instances "
                    "that have an invalid content type.\n"
                    "What would you like to do with them?"
                ) % {
                    "count": count,
                    "app_label": model._meta.app_label,
                    "model": model.__name__,
                },
                choices=["Skip", "Print", "Delete", "Exit"]
            )

            if action == "Exit":
                raise ExitException

            if action == "Print":
                print("-" * 48)
                for index, obj in enumerate(objects, start=1):
                    content_type_id = obj.collection_content_type_id
                    content_type = ContentType.objects.get_for_id(content_type_id)

                    number = "{})".format(index)
                    print(
                        "{:<3} \033[92m{}.{}\033[0m #{}\n"
                        "    ContentType ID: \033[91m{}\033[0m\n"
                        "    ContentType model: \033[91m{}.{}\033[0m\n"
                        "    Created at: {}".format(
                            number,
                            obj._meta.app_label,
                            obj.__class__.__name__,
                            obj.pk,
                            content_type_id,
                            content_type.app_label,
                            content_type.model,
                            obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    )
                print("-" * 48)
            elif action == "Delete":
                with transaction.atomic(using=self.database):
                    for obj in objects:
                        content_type_id = obj.collection_content_type_id
                        CollectionItemBase.objects.filter(
                            collection_content_type_id=content_type_id,
                            collection_id=obj.id
                        ).delete()

                        obj.delete()
                break
            else:
                break

    def clean_invalid_ownership(self):
        """
        Удаление ресурсов и коллекций, у которых:
        *) owner_app_label и owner_model_name, ссылаются на несуществующую модель
        *) имя поля, указанное в owner_fieldname отсутствует в классе модели владельца
        """
        if not self._check_ownership:
            self._step = Step.CHECK_FILES
            return

        for root in helpers.get_resource_model_trees():
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model
                self._clean_model_ownership(model)

        for root in helpers.get_collection_trees(include_proxy=True):
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model

                if model is Collection:
                    continue

                self._clean_model_ownership(model)

        self._step = Step.CHECK_FILES

    def _clean_model_ownership(self, model: Type[BacklinkModelMixin]):
        if not issubclass(model, BacklinkModelMixin):
            return

        query_fields = [
            "pk",
            "owner_app_label",
            "owner_model_name",
            "owner_fieldname"
        ]
        if issubclass(model, CollectionBase):
            query_fields.extend([
                "collection_content_type_id",
            ])

        created_before = now() - timedelta(seconds=self.options["min_age"])
        queryset = model.objects.using(self.database).filter(
            created_at__lte=created_before
        ).only(*query_fields)

        objects = set()
        for instance in queryset.iterator():
            owner_field = instance.get_owner_field()
            if owner_field is None:
                objects.add(instance)

        if not objects:
            return

        count = len(objects)
        while True:
            action = prompt_action(
                message=(
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m instance "
                    "that has an invalid owner reference.\n"
                    "What would you like to do with it?"
                    if count == 1 else
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m instances "
                    "that have an invalid owner reference.\n"
                    "What would you like to do with them?"
                ) % {
                    "count": count,
                    "app_label": model._meta.app_label,
                    "model": model.__name__,
                },
                choices=["Skip", "Print", "Delete", "Exit"]
            )

            if action == "Exit":
                raise ExitException

            if action == "Print":
                print("-" * 48)
                for index, obj in enumerate(objects, start=1):
                    number = "{})".format(index)
                    print(
                        "{:<3} \033[92m{}.{}\033[0m #{}\n"
                        "    Owner reference: \033[91m{}.{}\033[0m\n"
                        "    Owner field: \033[91m{}\033[0m\n"
                        "    Created at: {}".format(
                            number,
                            obj._meta.app_label,
                            obj.__class__.__name__,
                            obj.pk,
                            obj.owner_app_label,
                            obj.owner_model_name,
                            obj.owner_fieldname,
                            obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    )
                print("-" * 48)
            elif action == "Delete":
                with transaction.atomic(using=self.database):
                    # Каждый экземпляр должен быть удалён через свою прокси-модель,
                    # если такая есть. Поэтому удаление через QuerySet не допустимо.
                    for obj in objects:
                        obj.delete()
                break
            else:
                break

    def clean_file_existence(self):
        if not self._check_file_existence:
            self._step = Step.END
            return

        for root in helpers.get_resource_model_trees():
            for node in reversed(tuple(LevelOrderIter(root))):
                model = node.model
                self._clean_file_existence(model)

        self._step = Step.END

    def _clean_file_existence(self, model: Type[FileResource]):
        if not issubclass(model, FileResource):
            return

        created_before = now() - timedelta(seconds=self.options["min_age"])
        queryset = model.objects.using(self.database).filter(
            created_at__lte=created_before
        )

        objects = set()
        for instance in queryset.iterator():
            if not instance.file_exists():
                objects.add(instance)

        if not objects:
            return

        count = len(objects)
        while True:
            action = prompt_action(
                message=(
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m instance "
                    "that refers to a file that does not exist.\n"
                    "What would you like to do with it?"
                    if count == 1 else
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m instances "
                    "that refer to a file that does not exist.\n"
                    "What would you like to do with them?"
                ) % {
                    "count": count,
                    "app_label": model._meta.app_label,
                    "model": model.__name__,
                },
                choices=["Skip", "Print", "Delete", "Exit"]
            )

            if action == "Exit":
                raise ExitException

            if action == "Print":
                print("-" * 48)
                for index, obj in enumerate(objects, start=1):
                    number = "{})".format(index)
                    print(
                        "{:<3} \033[92m{}.{}\033[0m #{}\n"
                        "    Created at: {}".format(
                            number,
                            obj._meta.app_label,
                            obj.__class__.__name__,
                            obj.pk,
                            obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    )
                print("-" * 48)
            elif action == "Delete":
                with transaction.atomic(using=self.database):
                    # Каждый экземпляр должен быть удалён через свою прокси-модель,
                    # если такая есть. Поэтому удаление через QuerySet не допустимо.
                    for obj in objects:
                        obj.delete()
                break
            else:
                break
