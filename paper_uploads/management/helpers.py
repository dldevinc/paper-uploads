import logging
import sys
from datetime import timedelta

from anytree import LevelOrderIter
from django.core.management import color_style
from django.db import DEFAULT_DB_ALIAS
from django.utils.timezone import now

from .. import helpers
from . import utils


def remove_empty_collections(
    threshold: int = 24 * 3600,
    database: str = DEFAULT_DB_ALIAS,
    verbosity: int = logging.ERROR
):
    """
    Удаление коллекций, которые не содержат элементов.

    Удалять недавно созданные коллекции нельзя, т.к. они могут быть в процессе
    заполнения другим пользователем.

    :param threshold: минимальное время с момента создания коллекции в секундах
    :param database: алиас базы данных для поиска коллекций
    :param verbosity: уровень логирования
    :returns: количество удалённых коллекций
    """
    deleted = 0
    style = color_style()

    for root in helpers.get_collection_trees():
        for node in reversed(tuple(LevelOrderIter(root))):
            model = node.model

            created_before = now() - timedelta(seconds=threshold)
            queryset = model.objects.using(database).filter(
                items=None,
                created_at__lte=created_before
            )

            count = queryset.count()
            if not count:
                continue

            if verbosity <= logging.DEBUG:
                print(
                    "Removing {count} {verb} of {target} ...".format(
                        count=style.WARNING(count),
                        verb="instance" if count == 1 else "instances",
                        target=style.NOTICE(
                            "{}.{}".format(
                                model._meta.app_label,
                                model.__name__,
                            )
                        )
                    ),
                    end=" "
                )

            queryset.delete()

            if verbosity <= logging.DEBUG:
                print(style.WARNING("ok"))

            deleted += count

    return deleted


def create_missing_variations(
    async_: bool = False,
    database: str = DEFAULT_DB_ALIAS,
    verbosity: int = logging.ERROR
):
    """
    Создание отсутствующих файлов вариаций.

    :param async_: использовать django-rq для создания файлов вариаций
    :param database: алиас базы данных для поиска файлов
    :param verbosity: уровень логирования
    :returns: количество созданных файлов
    """
    variations_created = 0
    style = color_style()

    for node in helpers.get_resource_model_trees():
        model = node.model

        if not utils.is_variations_allowed(model):
            continue

        for instance in model.objects.using(database).iterator():

            missing_variations = []
            for vname, vfile in instance.variation_files():
                if vfile is not None and not vfile.exists():
                    missing_variations.append(vname)

            if missing_variations and instance.file_exists():
                count = len(missing_variations)

                if verbosity <= logging.DEBUG:
                    print(
                        "Creating {count} {verb} for {target} ...".format(
                            count=style.WARNING(count),
                            verb="variation" if count == 1 else "variations",
                            target=style.NOTICE(
                                "{}.{} #{}".format(
                                    model._meta.app_label,
                                    model.__name__,
                                    instance.pk
                                )
                            )
                        ),
                        end=" "
                    )
                    sys.stdout.flush()

                if async_:
                    instance.recut_async(names=missing_variations)
                else:
                    instance.recut(names=missing_variations)

                if verbosity <= logging.DEBUG:
                    print(style.WARNING("ok"))
                    sys.stdout.flush()

                variations_created += count

    return variations_created
