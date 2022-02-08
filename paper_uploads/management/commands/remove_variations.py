import sys
from typing import Iterable, Type

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from ...models.base import Resource
from ...models.collection import CollectionBase
from .. import utils


class Command(BaseCommand):
    help = """
    Удаление вариаций для всех экземпляров указанной модели.
    
    Примеры:
        python3 manage.py remove_variations blog.post --field=hero
        python3 manage.py remove_variations blog.gallery --item-type=image
    """
    options = None
    verbosity = None
    database = DEFAULT_DB_ALIAS
    interactive = False

    def add_arguments(self, parser):
        parser.add_argument(
            "model",
            metavar="app_label.ModelName",
            help="Specifies the model to remove variations from",
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
            help="Specifies the variation names to delete",
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
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]
        self.interactive = options["interactive"]

        model = apps.get_model(self.options["model"])
        if utils.is_collection(model):
            self.process_collection(model)
        else:
            self.process_resource(model)

    def process_collection(self, model: Type[CollectionBase]):
        item_type = self.options["item_type"]
        if not item_type:
            raise RuntimeError("The argument 'item-type' is required")

        if item_type not in model.item_types:
            raise RuntimeError("Unsupported collection item type: %s" % item_type)

        item_type_field = model.item_types[item_type]
        if not utils.is_variations_allowed(item_type_field.model):
            raise RuntimeError("Specified collection item type has no variations: %s" % item_type)

        variations = self.options["variations"]
        if not variations:
            if self.interactive:
                variations = self.variations_dialog(model, item_type_field)

        if not variations:
            variations = set(utils.get_collection_variations(model, item_type_field))

        self._process_collection(model, item_type, variations)

    def _process_collection(self, model: Type[CollectionBase], item_type: str, variations: Iterable[str]):
        queryset = model.objects.using(self.database)

        total = queryset.count()
        for index, collection in enumerate(queryset.iterator(), start=1):
            if self.verbosity >= 1:
                self.stdout.write(
                    "Remove variations for \033[92m'{}.{}'\033[0m (ID: {}) ({}/{}) ... ".format(
                        model._meta.app_label,
                        model.__name__,
                        collection.pk,
                        index,
                        total
                    )
                )

            for item in collection.get_items(item_type).iterator():
                for variation_name in item.get_variations():
                    if variation_name in variations:
                        variation_file = item.get_variation_file(variation_name)
                        variation_file.delete()

    def process_resource(self, model: Type[Resource]):
        fieldname = self.options["field"]
        if not fieldname:
            raise RuntimeError("The argument 'field' is required")

        field = model._meta.get_field(fieldname)
        if field.is_relation and not utils.is_variations_allowed(field.related_model):
            raise RuntimeError("Specified field has no variations: %s" % fieldname)

        variations = self.options["variations"]
        if not variations:
            if self.interactive:
                variations = self.variations_dialog(model, field)

        if not variations:
            variations = set(utils.get_field_variations(field))

        self._process_resource(model, fieldname, variations)

    def _process_resource(self, model: Type[Resource], fieldname: str, variations: Iterable[str]):
        queryset = model.objects.using(self.database).exclude((fieldname, None))

        total = queryset.count()
        for index, instance in enumerate(queryset.iterator(), start=1):
            if self.verbosity >= 1:
                self.stdout.write(
                    "Remove variations for \033[92m'{}.{}'\033[0m (ID: {}) ({}/{}) ... ".format(
                        type(instance)._meta.app_label,
                        type(instance).__name__,
                        instance.pk,
                        index,
                        total
                    )
                )
            field = getattr(instance, fieldname)

            for variation_name in variations:
                if variation_name in field.get_variations():
                    variation_file = field.get_variation_file(variation_name)
                    variation_file.delete()

    def variations_dialog(self, model, field):
        if utils.is_collection(model):
            allowed_variations = utils.get_collection_variations(model, field)
        else:
            allowed_variations = utils.get_field_variations(field)

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
