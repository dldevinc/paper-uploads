import sys
from typing import List, Type, Union

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models.fields import Field

from ... import exceptions
from ...models.base import VersatileImageResourceMixin
from ...models.collection import Collection
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


def is_collection(model: Type[Union[models.Model, Collection]]) -> bool:
    """
    Возвращает True, если model - коллекция.
    """
    return issubclass(model, Collection)


def get_collection_variations(model: Type[Collection], item_type_class: CollectionItem) -> List[str]:
    return list(
        item_type_class.model.get_variation_config(item_type_class, model).keys()
    )


def get_field_variations(field: VersatileImageResourceMixin) -> List[str]:
    return list(
        field.variations.keys()
    )


class Command(BaseCommand):
    help = """
    Создание/перезапись вариаций для указанной модели из исходного изображения.
    """
    verbosity = None
    database = DEFAULT_DB_ALIAS

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
                 "You should not specify any field for Collection models.",
        )
        parser.add_argument(
            "--item-type",
            nargs="?",
            help="Only look for variations in the specified CollectionItem. "
                 "Use this argument for Collection models only.",
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

    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        self.database = options["database"]

        model_name = options["model"]
        model = apps.get_model(model_name)
        if is_collection(model):
            item_type = options["item_type"]
            if not item_type:
                raise RuntimeError("The argument 'item-type' required")

            if item_type not in model.item_types:
                raise RuntimeError("Unsupported collection item type: %s" % item_type)

            item_type_class = model.item_types[item_type]
            if not is_image_item(item_type_class):
                raise RuntimeError("Not an image or invalid collection item type: %s" % item_type)

            variations = options["variations"]
            if not variations:
                if options["interactive"]:
                    variations = self.select_variations_dialog(model, item_type_class)

            if not variations:
                variations = set(get_collection_variations(model, item_type_class))

            self.process_collection(model, item_type, variations)
        else:
            fieldname = options["field"]
            if not fieldname:
                raise RuntimeError("The argument 'field' required")

            field = model._meta.get_field(fieldname)
            if not is_image(field):
                raise RuntimeError("Not an image or invalid field: %s" % fieldname)

            variations = options["variations"]
            if not variations:
                if options["interactive"]:
                    variations = self.select_variations_dialog(model, field)

            if not variations:
                variations = set(get_field_variations(field))

            self.process_field(model, fieldname, variations)

    def process_collection(self, model, item_type, variations):
        total = model.objects.using(self.database).count()  # use `objects` manager!
        for index, collection in enumerate(
            model.objects.using(self.database).iterator(), start=1
        ):
            if self.verbosity >= 1:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Recreate variations for `{}` #{} ({}/{}) ... ".format(
                            model.__name__, collection.pk, index, total
                        )
                    )
                )

            for item in collection.get_items(item_type).using(self.database).iterator():
                try:
                    item.recut(names=variations)
                except exceptions.FileNotFoundError:
                    self.stderr.write(
                        "Not found source file for `{}` #{}".format(
                            item.__class__.__name__, item.pk
                        )
                    )

    def process_field(self, model, fieldname, variations):
        instances = model._base_manager.using(self.database).exclude(
            (fieldname, None)
        )
        total = instances.count()
        for index, instance in enumerate(instances.iterator(), start=1):
            if self.verbosity >= 1:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Recreate variations for `{}` #{} ({}/{}) ... ".format(
                            model.__name__, instance.pk, index, total
                        )
                    ),
                    ending="\r",
                )
            field = getattr(instance, fieldname)

            try:
                field.recut(names=variations)
            except exceptions.FileNotFoundError:
                self.stderr.write(
                    "Not found source file for `{}` #{}".format(
                        model.__name__, instance.pk
                    )
                )

        self.stdout.write("")

    def select_variations_dialog(self, model, field):
        if is_collection(model):
            allowed_variations = get_collection_variations(model, field)
        else:
            allowed_variations = get_field_variations(field)

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
