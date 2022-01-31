import sys
from typing import List, Type, Union

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models.fields import Field

from ...models.base import Resource, VersatileImageResourceMixin
from ...models.collection import CollectionBase
from ...models.fields.collection import CollectionItem


def is_image(field: Field) -> bool:
    """
    Возвращает True, если поле ссылается на класс изображения с вариациями.
    """
    return field.is_relation and issubclass(
        field.related_model, VersatileImageResourceMixin
    )


def is_image_item(field: CollectionItem) -> bool:
    """
    Возвращает True, если поле коллекции подключает класс элемента
    изображения с вариациями.
    """
    return issubclass(field.model, VersatileImageResourceMixin)


def is_collection(model: Type[Union[models.Model, CollectionBase]]) -> bool:
    """
    Возвращает True, если model - коллекция.
    """
    return issubclass(model, CollectionBase)


def get_collection_variations(model: Type[CollectionBase], item_type_class: CollectionItem) -> List[str]:
    return list(
        item_type_class.model.get_variation_config(item_type_class, model).keys()
    )


def get_resource_variations(field: Field) -> List[str]:
    return list(
        field.variations.keys()
    )


class Command(BaseCommand):
    help = """
    Создание/перезапись вариаций для всех экземпляров указанной модели.
    
    Примеры:
        python3 manage.py recreate_variations blog.post --field=hero
        python3 manage.py recreate_variations blog.gallery --item-type=image
    """
    options = None
    verbosity = None
    database = DEFAULT_DB_ALIAS
    interactive = False

    def add_arguments(self, parser):
        parser.add_argument(
            "model",
            metavar="app_label.ModelName",
            help="Specifies the model to recreate variations for",
        )
        parser.add_argument(
            "--field",
            nargs="?",
            help="Restricts variations to the specified field. "
                 "You should not specify this option for Collection models.",
        )
        parser.add_argument(
            "--item-type",
            nargs="?",
            help="Only look for variations in the specified CollectionItem. "
                 "Use this argument only for Collection models.",
        )
        parser.add_argument(
            "--variations",
            dest="variations",
            nargs="+",
            help="Specifies the variation names to recreate",
        )
        parser.add_argument(
            "-i", "--interactive",
            action="store_true",
        )
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates the database to use. Defaults to the 'default' database.",
        )

    def get_model(self):
        return apps.get_model(self.options["model"])

    def _process_collection(self, model: Type[CollectionBase], item_type: str, variations):
        collection_model = model.collection_content_type.model_class()
        queryset = collection_model.objects.using(self.database)

        total = queryset.count()
        for index, collection in enumerate(queryset.iterator(), start=1):
            if self.verbosity >= 1:
                self.stdout.write(
                    "Recreate variations for \033[92m'{}.{}'\033[0m (ID: {}) ({}/{}) ... ".format(
                        collection_model._meta.app_label,
                        collection_model.__name__,
                        collection.pk,
                        index,
                        total
                    )
                )

            for item in collection.get_items(item_type).iterator():
                try:
                    item.recut(names=variations)
                except FileNotFoundError:
                    self.stderr.write(
                        "File missing for '{}.{}' (ID: {item.pk})".format(
                            type(item)._meta.app_label,
                            type(item).__name__,
                            item=item
                        )
                    )

    def process_collection(self, model: Type[CollectionBase]):
        item_type = self.options["item_type"]
        if not item_type:
            raise RuntimeError("The argument 'item-type' is required")

        if item_type not in model.item_types:
            raise RuntimeError("Unsupported collection item type: %s" % item_type)

        item_type_field = model.item_types[item_type]
        if not is_image_item(item_type_field):
            raise RuntimeError("Specified collection item type has no variations: %s" % item_type)

        variations = self.options["variations"]
        if not variations:
            if self.interactive:
                variations = self.variations_dialog(model, item_type_field)

        if not variations:
            variations = set(get_collection_variations(model, item_type_field))

        self._process_collection(model, item_type, variations)

    def _process_resource(self, model: Type[Resource], fieldname, variations):
        queryset = model.objects.using(self.database).exclude((fieldname, None))

        total = queryset.count()
        for index, instance in enumerate(queryset.iterator(), start=1):
            if self.verbosity >= 1:
                self.stdout.write(
                    "Recreate variations for \033[92m'{}.{}'\033[0m (ID: {}) ({}/{}) ... ".format(
                        type(instance)._meta.app_label,
                        type(instance).__name__,
                        instance.pk,
                        index,
                        total
                    )
                )
            field = getattr(instance, fieldname)

            try:
                field.recut(names=variations)
            except FileNotFoundError:
                self.stderr.write(
                    "File missing for '{}.{}' (ID: {instance.pk})".format(
                        type(instance)._meta.app_label,
                        type(instance).__name__,
                        instance=instance
                    )
                )

    def process_resource(self, model: Type[Resource]):
        fieldname = self.options["field"]
        if not fieldname:
            raise RuntimeError("The argument 'field' is required")

        field = model._meta.get_field(fieldname)
        if not is_image(field):
            raise RuntimeError("Specified field has no variations: %s" % fieldname)

        variations = self.options["variations"]
        if not variations:
            if self.interactive:
                variations = self.variations_dialog(model, field)

        if not variations:
            variations = set(get_resource_variations(field))

        self._process_resource(model, fieldname, variations)

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]
        self.interactive = options["interactive"]

        model = self.get_model()
        if is_collection(model):
            self.process_collection(model)
        else:
            self.process_resource(model)

    def variations_dialog(self, model, field):
        if is_collection(model):
            allowed_variations = get_collection_variations(model, field)
        else:
            allowed_variations = get_resource_variations(field)

        while True:
            self.stdout.write(
                self.style.SUCCESS(
                    "Please, specify the variations you would like to process."
                )
            )
            self.stdout.write(" {}) All variations".format(self.style.SUCCESS("*")))
            for index, vname in enumerate(allowed_variations, start=1):
                self.stdout.write(
                    "{}) Variation `{}`".format(
                        self.style.SUCCESS("{:>2}".format(index)), vname
                    )
                )
            self.stdout.write(" {}) Abort".format(self.style.SUCCESS("q")))
            self.stdout.write("Enter your choice: ", ending="")

            answer_string = input().strip()
            answers = tuple(map(str.strip, answer_string.split(",")))
            if "*" in answers:
                return allowed_variations
            if "q" in answers:
                sys.exit()

            try:
                answers = tuple(map(int, answers))
            except ValueError:
                self.stderr.write(
                    "Invalid selection. Press Enter to try again... ", ending=""
                )
                input()
                continue

            if not all(1 <= answer <= len(allowed_variations) for answer in answers):
                self.stderr.write(
                    "Invalid selection. Press Enter to try again... ", ending=""
                )
                input()
                continue

            return set(allowed_variations[answer - 1] for answer in answers)
