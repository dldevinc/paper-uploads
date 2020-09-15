import sys
from itertools import chain
from typing import List, Tuple, Type, Union

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models.fields import Field
from django.db.models.utils import make_model_tuple
from paper_uploads.models import CollectionItem

from ...models.base import VersatileImageResourceMixin
from ...models.collection import Collection


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


def is_gallery(model: Type[Union[models.Model, Collection]]) -> bool:
    """
    Возвращает True, если model - коллекция, в которой есть
    хотя бы один класс элемента изображения с вариациями.
    """
    return issubclass(model, Collection) and any(
        is_image_item(field) for field in model.item_types.values()
    )


def get_allowed_models() -> Tuple[List[str], List[str]]:
    """
    Возвращает два списка моделей, для которых возможна перенарезка:
    список обычных моделей и список галерей.
    """
    regular_models = []
    gallery_models = []
    for app_conf in apps.get_app_configs():
        if app_conf.name == 'paper_uploads':
            continue

        for model in app_conf.get_models():
            if get_allowed_fields(model):
                if is_gallery(model):
                    gallery_models.append('{}.{}'.format(*make_model_tuple(model)))
                else:
                    regular_models.append('{}.{}'.format(*make_model_tuple(model)))
    return regular_models, gallery_models


def get_allowed_fields(model: Type[Union[models.Model, Collection]]) -> List[str]:
    """
    Для заданной модели возвращает список имен полей, хранящих
    ссылки на изображения с вариациями.
    """
    if is_gallery(model):
        return [
            name
            for name, field in model.item_types.items()
            if is_image_item(field) and get_allowed_variations(model, field)
        ]
    else:
        return [
            field.name
            for field in model._meta.get_fields()
            if is_image(field) and get_allowed_variations(model, field)
        ]


def get_allowed_variations(
    model: Type[Union[models.Model, Collection]],
    field: Union[VersatileImageResourceMixin, CollectionItem],
) -> List[str]:
    """
    Для заданного поля модели возвращает список имен вариаций
    """
    if is_gallery(model):
        if not is_image_item(field):
            raise TypeError("field '%s' refers to the non-image model" % field.name)
        return list(field.model.get_variation_config(field, model).keys())
    else:
        if not is_image(field):
            raise TypeError("field '%s' refers to the non-image model" % field.name)
        return list(field.variations.keys())


def get_regular_field(model: Type[models.Model], fieldname: str) -> Field:
    """
    Получение поля обычной модели
    """
    return model._meta.get_field(fieldname)


def get_itemtype_field(model: Type[Collection], fieldname: str) -> CollectionItem:
    """
    Получение поля коллекции
    """
    return model.item_types[fieldname]


class Command(BaseCommand):
    verbosity = None
    database = DEFAULT_DB_ALIAS

    def add_arguments(self, parser):
        parser.add_argument(
            'model',
            nargs='?',
            metavar='app_label.ModelName',
            help='Specify the model to recreate variations for',
        )
        parser.add_argument(
            'field',
            nargs='?',
            help='Restricts recreated variations to the specified field',
        )
        parser.add_argument(
            '--variations',
            dest='variations',
            nargs='+',
            help='Specify the variation names to recreate variations for',
        )
        parser.add_argument(
            '-i', '--interactive', action='store_true',
        )
        parser.add_argument(
            '--database',
            action='store',
            dest='database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates the database to use. Defaults to the "default" database.',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.database = options['database']

        model_name = options['model']
        fieldname = options['field']
        variations = options['variations']

        # select model
        if options['interactive']:
            model_name = self.select_model_dialog()
        elif model_name is None:
            raise RuntimeError('the following arguments are required: model')
        model = apps.get_model(model_name)

        # select field
        if options['interactive']:
            fieldname = self.select_field_dialog(model)
        elif fieldname is None:
            raise RuntimeError('the following arguments are required: field')
        if is_gallery(model):
            field = get_itemtype_field(model, fieldname)
        else:
            field = get_regular_field(model, fieldname)

        # select variations
        if options['interactive']:
            variations = self.select_variations_dialog(model, field)
        elif variations is None:
            variations = set(get_allowed_variations(model, field))

        # process
        if is_gallery(model):
            total = model.objects.using(self.database).count()  # use `objects` manager!
            for index, collection in enumerate(
                model.objects.using(self.database).iterator(), start=1
            ):
                if self.verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Recreate variations for `{}` #{} ({}/{}) ... ".format(
                                model_name, collection.pk, index, total
                            )
                        )
                    )

                for name, field in collection.item_types.items():
                    if is_image_item(field):
                        for item in collection.get_items().iterator():
                            item.recut(names=variations)
        else:
            instances = model._base_manager.using(self.database).exclude(
                (fieldname, None)
            )
            total = instances.count()
            for index, instance in enumerate(instances, start=1):
                if self.verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Recreate variations for `{}` #{} ({}/{}) ... ".format(
                                model_name, instance.pk, index, total
                            )
                        ),
                        ending='\r',
                    )
                field = getattr(instance, fieldname)
                field.recut(names=variations)
            self.stdout.write('')

    def select_model_dialog(self):
        while True:
            regular, galleries = get_allowed_models()
            allowed_models = tuple(chain(regular, galleries))

            self.stdout.write(
                self.style.SUCCESS(
                    'Please, specify the MODEL you would like to process.'
                )
            )
            for index, modelname in enumerate(allowed_models, start=1):
                self.stdout.write(
                    '{}) Model `{}`'.format(
                        self.style.SUCCESS('{:>2}'.format(index)), modelname
                    )
                )
            self.stdout.write(' {}) Exit'.format(self.style.SUCCESS('0')))

            answer = input().strip()
            if answer == '0':
                sys.exit()

            try:
                answer = int(answer)
            except ValueError:
                self.stderr.write(
                    'Invalid selection. Press Enter to try again... ', ending=''
                )
                input()
                continue

            if not 1 <= answer <= len(allowed_models):
                self.stderr.write(
                    'Invalid selection. Press Enter to try again... ', ending=''
                )
                input()
                continue

            return allowed_models[answer - 1]

    def select_field_dialog(self, model):
        while True:
            allowed_fields = get_allowed_fields(model)

            self.stdout.write(
                self.style.SUCCESS(
                    'Please, specify the FIELD you would like to process.'
                )
            )
            for index, fieldname in enumerate(allowed_fields, start=1):
                self.stdout.write(
                    '{}) Field `{}`'.format(
                        self.style.SUCCESS('{:>2}'.format(index)), fieldname
                    )
                )
            self.stdout.write(' {}) Exit'.format(self.style.SUCCESS('0')))

            answer = input().strip()
            if answer == '0':
                sys.exit()

            try:
                answer = int(answer)
            except ValueError:
                self.stderr.write(
                    'Invalid selection. Press Enter to try again... ', ending=''
                )
                input()
                continue

            if not 1 <= answer <= len(allowed_fields):
                self.stderr.write(
                    'Invalid selection. Press Enter to try again... ', ending=''
                )
                input()
                continue

            return allowed_fields[answer - 1]

    def select_variations_dialog(self, model, field):
        while True:
            allowed_variations = get_allowed_variations(model, field)

            self.stdout.write(
                self.style.SUCCESS(
                    'Please, specify the VARIATIONS you would like to process.'
                )
            )
            self.stdout.write(' {}) All variations'.format(self.style.SUCCESS('*')))
            for index, vname in enumerate(allowed_variations, start=1):
                self.stdout.write(
                    '{}) Variation `{}`'.format(
                        self.style.SUCCESS('{:>2}'.format(index)), vname
                    )
                )
            self.stdout.write(' {}) Exit'.format(self.style.SUCCESS('0')))

            answer = input().strip()
            answers = tuple(map(str.strip, answer.split(',')))
            if '0' in answers:
                sys.exit()
            if '*' in answers:
                return allowed_variations

            try:
                answers = tuple(map(int, answers))
            except ValueError:
                self.stderr.write(
                    'Invalid selection. Press Enter to try again... ', ending=''
                )
                input()
                continue

            if not all(1 <= answer <= len(allowed_variations) for answer in answers):
                self.stderr.write(
                    'Invalid selection. Press Enter to try again... ', ending=''
                )
                input()
                continue

            return set(allowed_variations[answer - 1] for answer in answers)
