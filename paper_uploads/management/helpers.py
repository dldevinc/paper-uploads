import operator
import sys
from collections import namedtuple
from datetime import timedelta
from itertools import groupby
from typing import Any, Callable, Generator, List, Tuple, Type, Union

from anytree import LevelOrderIter
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS, models
from django.utils.timezone import now

from .. import helpers
from ..models.base import Resource
from ..models.collection import Collection, CollectionBase, CollectionItemBase
from . import utils
from .prompt import prompt_action, prompt_variants

ModelChoice = namedtuple("ModelChoice", ["name", "type"])
ItemTypeChoice = namedtuple("ItemTypeChoice", ["name", "field"])
FieldChoice = namedtuple("FieldChoice", ["name", "field"])
VariationChoice = namedtuple("VariationChoice", ["name", "size"])


def find_empty_collections(
    min_age: int = 24 * 3600,
    database: str = DEFAULT_DB_ALIAS,
) -> Generator[models.QuerySet[Collection], Any, None]:
    """
    Поиск коллекций, которые не содержат элементов.

    Для того, чтобы не удалить коллекции, которые созданы недавно и ещё не
    заполнены, можно воспользоваться параметром `min_age`. Он задаёт минимальный
    возраст коллекции в секундах.

    :param min_age: минимальное время с момента создания коллекции в секундах.
    :param database: алиас базы данных для поиска коллекций.
    """
    for root in helpers.get_collection_trees():
        for node in reversed(tuple(LevelOrderIter(root))):
            model = node.model
            concrete_ct = ContentType.objects.db_manager(using=database).get_for_model(model)

            created_before = now() - timedelta(seconds=min_age)
            queryset = model.objects.using(database).filter(
                ~models.Exists(CollectionItemBase.objects.using(database).filter(
                    concrete_collection_content_type=concrete_ct,
                    collection_id=models.OuterRef("pk")
                )),
                concrete_collection_content_type=concrete_ct,
                created_at__lte=created_before
            ).select_related(
                "collection_content_type"
            ).only(
                "id", "collection_content_type"
            ).order_by("collection_content_type_id")

            if queryset.exists():
                for ct, group in groupby(queryset.iterator(), key=lambda x: x.collection_content_type):
                    collection_cls = ct.model_class()
                    ids = set(item.pk for item in group)
                    yield collection_cls.objects.using(database).filter(pk__in=ids)


def remove_empty_collections(
    min_age: int = 24 * 3600,
    database: str = DEFAULT_DB_ALIAS
):
    """
    Удаление коллекций, которые не содержат элементов.

    Удалять недавно созданные коллекции нельзя, т.к. они могут быть в процессе
    заполнения другим пользователем.

    :param min_age: минимальное время с момента создания коллекции в секундах.
    :param database: алиас базы данных для поиска коллекций.
    """
    for collection_qs in find_empty_collections(min_age=min_age, database=database):
        collection_cls = collection_qs.model
        count = collection_qs.count()

        while True:
            action = prompt_action(
                message=(
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m collection "
                    "that do not have any elements.\n"
                    "What would you like to do with it?"
                    if count == 1 else
                    "Found \033[92m%(count)d %(app_label)s.%(model)s\033[0m collections "
                    "that do not have any elements.\n"
                    "What would you like to do with them?"
                ) % {
                    "count": count,
                    "app_label": collection_cls._meta.app_label,
                    "model": collection_cls.__name__,
                },
                choices=["Skip", "Print", "Delete", "Exit"]
            )

            if action == "Print":
                print("-" * 48)
                for index, obj in enumerate(collection_qs.iterator(), start=1):
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
                collection_qs.delete()
                break
            elif action == "Skip":
                break
            else:
                return


def find_missing_variations(
    database: str = DEFAULT_DB_ALIAS
) -> Generator[Tuple[Resource, List[str]], Any, None]:
    """
    Поиск экземпляров изображений, для которых отсутствует хотя бы один
    файл вариации.

    :param database: алиас базы данных для поиска коллекций.
    """
    for root in helpers.get_resource_model_trees():
        for node in reversed(tuple(LevelOrderIter(root))):
            model = node.model

            if not utils.is_variations_allowed(model):
                continue

            for instance in model.objects.using(database).iterator():
                missing_variations = []
                for vname, vfile in instance.variation_files():
                    if not vfile.exists():
                        missing_variations.append(vname)

                if missing_variations and instance.file_exists():
                    yield instance, missing_variations


def create_missing_variations(
    async_: bool = False,
    database: str = DEFAULT_DB_ALIAS
):
    """
    Создание отсутствующих файлов вариаций.

    :param async_: использовать django-rq для создания файлов вариаций.
    :param database: алиас базы данных для поиска файлов.
    """
    for instance, missing_variations in find_missing_variations(database):
        count = len(missing_variations)

        print(
            "Creating \033[92m%(count)d\033[0m %(label)s"
            " for \033[92m%(app_label)s.%(model)s\033[0m #%(pk)s ... " % {
                "count": count,
                "label": "variation" if count == 1 else "variations",
                "app_label": type(instance)._meta.app_label,
                "model": type(instance).__name__,
                "pk": instance.pk
            },
            end=""
        )
        sys.stdout.flush()

        if async_:
            instance.recut_async(names=missing_variations)
        else:
            instance.recut(names=missing_variations)

        print("done")
        sys.stdout.flush()


def select_resource_model(
    message: str = None,
    multiple: bool = False,
    predicate: Callable = None,
    prepend_choices: List[str] = None,
    append_choices: List[str] = None,
    default: Union[str, List[str]] = None
) -> Union[None, str, List[str]]:
    """
    Диалог выбора одной или нескольких моделей, связанных с файловыми ресурсами.

    В списке выводятся регулярные модели, содержащие хотя бы одно поле,
    ссылающееся на подкласс Resource, а также модели коллекций.

    Пример:
        from paper_uploads.management.helpers import *
        from paper_uploads.management import utils

        model = select_resource_model()
        if model is None:
            print("Cancelled by user")
        elif utils.is_collection(model):
            item_type = select_collection_item_type(model)
            if item_type is None:
                print("Cancelled by user")
            else:
                variation_name = select_collection_variations(model, item_type)
        else:
            field_name = select_resource_field(model)
            if field_name is None:
                print("Cancelled by user")
            else:
                variation_name = select_resource_variations(model, field_name)
    """
    choices_data = []
    for model in apps.get_models():
        opts = model._meta

        if predicate is not None and not predicate(model):
            continue

        for field in opts.get_fields(include_hidden=True):
            if not utils.is_resource_field(field):
                continue

            choices_data.append(
                ModelChoice(
                    name="{}.{}".format(opts.app_label, opts.model_name),
                    type="Regular",
                )
            )
            break

    collection_models = (
        node.model
        for root in helpers.get_collection_trees(include_proxy=True)
        for node in reversed(tuple(LevelOrderIter(root)))
    )
    for model in collection_models:
        opts = model._meta

        if predicate is not None and not predicate(model):
            continue

        choices_data.append(
            ModelChoice(
                name="{}.{}".format(opts.app_label, opts.model_name),
                type="Collection",
            )
        )

    choices_data = sorted(
        choices_data,
        key=operator.attrgetter("name")
    )

    # Оформление опций в виде двух колонок.
    rows = []
    max_model_length = max((len(record.name) for record in choices_data), default=0)
    max_model_length = min(max(max_model_length, 10), 48)
    for choice in choices_data:
        rows.append((
            "{:<{width}} {}".format(
                choice.name,
                choice.type,
                width=max_model_length + 1
            ),
            choice.name
        ))

    if prepend_choices:
        rows = list(prepend_choices) + rows

    if append_choices:
        rows.extend(append_choices)

    if not rows:
        return

    if multiple:
        return prompt_variants(
            message=message or (
                "Select one or more models:\n"
                "   {column_name:<{width}} Type\n"
                "   {line}".format(
                    column_name="Model",
                    line="-" * (max_model_length + 16),
                    width=max_model_length + 1
                )
            ),
            choices=rows,
            default=default
        )
    else:
        return prompt_action(
            message=message or (
                "Select model:\n"
                "   {column_name:<{width}} Type\n"
                "   {line}".format(
                    column_name="Model",
                    line="-" * (max_model_length + 16),
                    width=max_model_length + 1
                )
            ),
            choices=rows,
            default=default
        )


def select_collection_item_type(
    collection: Type[CollectionBase],
    message: str = None,
    multiple: bool = False,
    predicate: Callable = None,
    prepend_choices: List[str] = None,
    append_choices: List[str] = None,
    default: Union[str, List[str]] = None
) -> Union[None, str, List[str]]:
    """
    Диалог выбора одного или нескольких типов элементов коллекции.
    """
    choices_data = []
    for name, field in collection.item_types.items():
        if predicate is not None and not predicate(field):
            continue

        choices_data.append(
            ItemTypeChoice(
                name=name,
                field=field
            )
        )

    choices_data = sorted(
        choices_data,
        key=operator.attrgetter("name")
    )

    # Оформление опций в виде двух колонок.
    rows = []
    max_name_length = max((len(record.name) for record in choices_data), default=0)
    max_name_length = min(max(max_name_length, 10), 48)
    for choice in choices_data:
        rows.append((
            "{:<{width}} {}".format(
                choice.name,
                choice.field.model.__name__,
                width=max_name_length + 1
            ),
            choice.name
        ))

    if prepend_choices:
        rows = list(prepend_choices) + rows

    if append_choices:
        rows.extend(append_choices)

    if not rows:
        return

    if multiple:
        return prompt_variants(
            message=message or (
                "Select one or more item types:\n"
                "   {column_name:<{width}} Model\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 16),
                    width=max_name_length + 1
                )
            ),
            choices=rows,
            default=default
        )
    else:
        return prompt_action(
            message=message or (
                "Select item type:\n"
                "   {column_name:<{width}} Model\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 16),
                    width=max_name_length + 1
                )
            ),
            choices=rows,
            default=default
        )


def select_resource_field(
    model: Type[models.Model],
    message: str = None,
    multiple: bool = False,
    predicate: Callable = None,
    prepend_choices: List[str] = None,
    append_choices: List[str] = None,
    default: Union[str, List[str]] = None
) -> Union[None, str, List[str]]:
    """
    Диалог выбора одного или нескольких полей, связанных с типом Resource.
    """
    choices_data = []
    for field in model._meta.get_fields(include_hidden=True):
        if not utils.is_resource_field(field):
            continue

        if predicate is not None and not predicate(field):
            continue

        choices_data.append(
            FieldChoice(
                name=field.name,
                field=field
            )
        )

    choices_data = sorted(
        choices_data,
        key=operator.attrgetter("name")
    )

    # Оформление опций в виде двух колонок.
    rows = []
    max_name_length = max((len(record.name) for record in choices_data), default=0)
    max_name_length = min(max(max_name_length, 10), 48)
    for choice in choices_data:
        rows.append((
            "{:<{width}} {}".format(
                choice.name,
                type(choice.field).__name__,
                width=max_name_length + 1
            ),
            choice.name
        ))

    if prepend_choices:
        rows = list(prepend_choices) + rows

    if append_choices:
        rows.extend(append_choices)

    if not rows:
        return

    if multiple:
        return prompt_variants(
            message=message or (
                "Select one or more resource fields:\n"
                "   {column_name:<{width}} Class\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 16),
                    width=max_name_length + 1
                )
            ),
            choices=rows,
            default=default
        )
    else:
        return prompt_action(
            message=message or (
                "Select resource field:\n"
                "   {column_name:<{width}} Class\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 16),
                    width=max_name_length + 1
                )
            ),
            choices=rows,
            default=default
        )


def select_collection_variations(
    collection: Type[CollectionBase],
    item_type: str,
    message: str = None,
    multiple: bool = False,
    predicate: Callable = None,
    prepend_choices: List[str] = None,
    append_choices: List[str] = None,
    default: Union[str, List[str]] = None
) -> Union[None, str, List[str]]:
    """
    Диалог выбора одной или нескольких вариаций элемента коллекции.
    """
    if item_type not in collection.item_types:
        raise RuntimeError("Unsupported collection item type: %s" % item_type)

    item_type_field = collection.item_types[item_type]
    if not utils.is_variations_allowed(item_type_field.model):
        raise RuntimeError("The specified collection item type does not support variations: %s" % item_type)

    choices_data = []
    for name, variation in utils.get_collection_variations(collection, item_type_field).items():
        if predicate is not None and not predicate(variation):
            continue

        choices_data.append(
            VariationChoice(
                name=name,
                size="×".join(map(str, variation.size))
            )
        )

    choices_data = sorted(
        choices_data,
        key=operator.attrgetter("name")
    )

    # Оформление опций в виде двух колонок.
    rows = []
    max_name_length = max((len(record.name) for record in choices_data), default=0)
    max_name_length = min(max(max_name_length, 10), 48)
    for choice in choices_data:
        rows.append((
            "{:<{width}} {}".format(
                choice.name,
                choice.size,
                width=max_name_length + 1
            ),
            choice.name
        ))

    rows = sorted(rows)

    if prepend_choices:
        rows = list(prepend_choices) + rows

    if append_choices:
        rows.extend(append_choices)

    if not rows:
        return

    if multiple:
        return prompt_variants(
            message=message or (
                "Select one or more variations:\n"
                "   {column_name:<{width}} Size\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 10),
                    width=max_name_length + 3
                )
            ),
            choices=rows,
            default=default
        )
    else:
        return prompt_action(
            message=message or (
                "Select variation:\n"
                "   {column_name:<{width}} Size\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 10),
                    width=max_name_length + 1
                )
            ),
            choices=rows,
            default=default
        )


def select_resource_variations(
    model: Type[models.Model],
    field_name: str,
    message: str = None,
    multiple: bool = False,
    predicate: Callable = None,
    prepend_choices: List[str] = None,
    append_choices: List[str] = None,
    default: Union[str, List[str]] = None
) -> Union[None, str, List[str]]:
    """
    Диалог выбора одной или нескольких вариаций изображения.
    """
    field = model._meta.get_field(field_name)

    if not utils.is_resource_field(field) or not utils.is_variations_allowed(field.related_model):
        raise RuntimeError("The specified field does not support variations: %s" % field.name)

    choices_data = []
    for name, variation in utils.get_field_variations(field).items():
        if predicate is not None and not predicate(variation):
            continue

        choices_data.append(
            VariationChoice(
                name=name,
                size="×".join(map(str, variation.size))
            )
        )

    choices_data = sorted(
        choices_data,
        key=operator.attrgetter("name")
    )

    # Оформление опций в виде двух колонок.
    rows = []
    max_name_length = max((len(record.name) for record in choices_data), default=0)
    max_name_length = min(max(max_name_length, 10), 48)
    for choice in choices_data:
        rows.append((
            "{:<{width}} {}".format(
                choice.name,
                choice.size,
                width=max_name_length + 1
            ),
            choice.name
        ))

    rows = sorted(rows)

    if prepend_choices:
        rows = list(prepend_choices) + rows

    if append_choices:
        rows.extend(append_choices)

    if not rows:
        return

    if multiple:
        return prompt_variants(
            message=message or (
                "Select one or more variations:\n"
                "   {column_name:<{width}} Size\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 10),
                    width=max_name_length + 3
                )
            ),
            choices=rows,
            default=default
        )
    else:
        return prompt_action(
            message=message or (
                "Select variation:\n"
                "   {column_name:<{width}} Size\n"
                "   {line}".format(
                    column_name="Name",
                    line="-" * (max_name_length + 10),
                    width=max_name_length + 1
                )
            ),
            choices=rows,
            default=default
        )
