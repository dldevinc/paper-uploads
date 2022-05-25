import sys
from enum import Enum, auto

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from paper_uploads.management import helpers

from .. import utils


class Step(Enum):
    GET_MODEL = auto()
    GET_FIELD = auto()
    GET_VARIATIONS = auto()
    PROCESS = auto()
    END = auto()


class ExitException(Exception):
    pass


class Command(BaseCommand):
    help = """
    Создание/перезапись вариаций для всех экземпляров указанной модели.
    
    Пример для обычной модели:
        python3 manage.py recreate_variations blog.post --field=hero
        
    Пример для коллекции:
        python3 manage.py recreate_variations blog.gallery --item-type=image
    """
    options = None
    verbosity = None
    database = DEFAULT_DB_ALIAS

    _step = Step.GET_MODEL
    _model = None
    _is_collection = None
    _field_name = None
    _variation_names = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            metavar="[APP_LABEL].[MODEL_NAME]",
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
                 "Use this argument for Collection models only.",
        )
        parser.add_argument(
            "--variations",
            dest="variations",
            nargs="+",
            help="Specifies the variation names to recreate",
        )
        parser.add_argument(
            "--async",
            action="store_true",
            help="Use django-rq to create variation files",
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

        try:
            self.loop()
        except ExitException:
            return

    def loop(self):
        while True:
            if self._step is Step.GET_MODEL:
                self.get_model()
            elif self._step is Step.GET_FIELD:
                if self._is_collection:
                    self.get_collection_field()
                else:
                    self.get_resource_field()
            elif self._step is Step.GET_VARIATIONS:
                if self._is_collection:
                    self.get_collection_variations()
                else:
                    self.get_resource_variations()
            elif self._step is Step.PROCESS:
                if self._is_collection:
                    self.process_collection()
                else:
                    self.process_resource()
            else:
                return

    def get_model(self):
        model_name = self.options["model"]
        if model_name is None:
            model_name = helpers.select_resource_model(
                append_choices=["[Exit]"]
            )

        if model_name == "[Exit]":
            raise ExitException

        self._model = apps.get_model(model_name)
        self._is_collection = utils.is_collection(self._model)
        self._step = Step.GET_FIELD

    def get_collection_field(self):
        item_type = self.options["item_type"]
        if item_type is None:
            item_type = helpers.select_collection_item_type(
                self._model,
                predicate=lambda f: utils.is_variations_allowed(f.model),
                append_choices=["[Back]", "[Exit]"]
            )

        if item_type == "[Exit]":
            raise ExitException

        if item_type == "[Back]":
            self._step = Step.GET_MODEL
            return

        self._field_name = item_type
        self._step = Step.GET_VARIATIONS

    def get_resource_field(self):
        field_name = self.options["field"]
        if field_name is None:
            field_name = helpers.select_resource_field(
                self._model,
                predicate=lambda f: utils.is_variations_allowed(f.related_model),
                append_choices=["[Back]", "[Exit]"]
            )

        if field_name == "[Exit]":
            raise ExitException

        if field_name == "[Back]":
            self._step = Step.GET_MODEL
            return

        self._field_name = field_name
        self._step = Step.GET_VARIATIONS

    def get_collection_variations(self):
        variations = self.options["variations"]
        if variations is None:
            variations = helpers.select_collection_variations(
                self._model,
                self._field_name,
                multiple=True,
                prepend_choices=["[All]"],
                append_choices=["[Back]", "[Exit]"]
            )

        if "[Exit]" in variations:
            raise ExitException

        if "[Back]" in variations:
            self._step = Step.GET_FIELD
            return

        if "[All]" in variations:
            item_type_field = self._model.item_types[self._field_name]
            self._variation_names = set(utils.get_collection_variations(
                self._model,
                item_type_field
            ))
        else:
            self._variation_names = set(variations)

        self._step = Step.PROCESS

    def get_resource_variations(self):
        variations = self.options["variations"]
        if variations is None:
            variations = helpers.select_resource_variations(
                self._model,
                self._field_name,
                multiple=True,
                prepend_choices=["[All]"],
                append_choices=["[Back]", "[Exit]"]
            )

        if "[Exit]" in variations:
            raise ExitException

        if "[Back]" in variations:
            self._step = Step.GET_FIELD
            return

        if "[All]" in variations:
            field = self._model._meta.get_field(self._field_name)
            self._variation_names = set(utils.get_field_variations(field))
        else:
            self._variation_names = set(variations)

        self._step = Step.PROCESS

    def process_collection(self):
        if not self._variation_names:
            return

        queryset = self._model.objects.using(self.database)

        total = queryset.count()
        for index, collection in enumerate(queryset.iterator(), start=1):
            collection_items = collection.get_items(self._field_name)
            collection_item_count = collection_items.count()
            if not collection_item_count:
                continue

            print(
                "Processing \033[92m{}\033[0m items"
                " of \033[92m'{}.{}'\033[0m (ID: {}) ({}/{}) ... ".format(
                    collection_item_count,
                    self._model._meta.app_label,
                    self._model.__name__,
                    collection.pk,
                    index,
                    total
                ),
                end=""
            )
            sys.stdout.flush()

            async_ = self.options["async"]

            for item in collection_items.iterator():
                if async_:
                    item.recut_async(names=self._variation_names)
                else:
                    try:
                        item.recut(names=self._variation_names)
                    except FileNotFoundError:
                        print(
                            "\n"
                            "\033[91mFile missing for '{}.{}' (ID: {})\033[0m".format(
                                type(item)._meta.app_label,
                                type(item).__name__,
                                item.pk
                            )
                        )
                        raise ExitException

            print("done")
            sys.stdout.flush()

        self._step = Step.END

    def process_resource(self):
        if not self._variation_names:
            return

        queryset = self._model.objects.using(self.database).exclude((self._field_name, None))

        total = queryset.count()
        for index, instance in enumerate(queryset.iterator(), start=1):
            print(
                "Processing \033[92m'{}.{}'\033[0m (ID: {}) ({}/{}) ... ".format(
                    type(instance)._meta.app_label,
                    type(instance).__name__,
                    instance.pk,
                    index,
                    total
                ),
                end=""
            )
            sys.stdout.flush()

            async_ = self.options["async"]
            field = getattr(instance, self._field_name)

            if async_:
                field.recut_async(names=self._variation_names)
            else:
                try:
                    field.recut(names=self._variation_names)
                except FileNotFoundError:
                    print(
                        "\n"
                        "\033[91mFile missing for '{}.{}' (ID: {})\033[0m".format(
                            type(instance)._meta.app_label,
                            type(instance).__name__,
                            instance.pk,
                        )
                    )
                    raise ExitException

            print("done")
            sys.stdout.flush()

        self._step = Step.END
