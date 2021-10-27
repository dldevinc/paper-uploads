from datetime import timedelta

from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from django.utils.timezone import now

from ...models.collection import Collection


class Command(BaseCommand):
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
            "--dry-run", action="store_true",
            help="Just show what collections would be deleted; don't actually delete them.",
        )
        parser.add_argument(
            "--min-age",
            type=int,
            default=3600,
            help="Minimum instance age in seconds to look for",
        )

    def remove_collections(self):
        min_age = now() - timedelta(seconds=self.options["min_age"])

        for model in apps.get_models():
            if not issubclass(model, Collection):
                continue

            queryset = model.objects.using(self.database).filter(
                items=None,
                created_at__lte=min_age
            )

            total = queryset.count()
            if not total:
                continue

            if self.options["dry_run"]:
                self.stdout.write(
                    "Found {count} empty {verb} of {classname}.".format(
                        count=self.style.SUCCESS(total),
                        verb="instance" if total == 1 else "instances",
                        classname=self.style.SUCCESS(
                            "{}.{}".format(
                                model._meta.app_label,
                                model.__name__,
                            )
                        )
                    )
                )
            else:
                queryset.delete()
                self.stdout.write(
                    "Deleted {count} empty {verb} of {classname}.".format(
                        count=self.style.SUCCESS(total),
                        verb="instance" if total == 1 else "instances",
                        classname=self.style.SUCCESS(
                            "{}.{}".format(
                                model._meta.app_label,
                                model.__name__,
                            )
                        )
                    )
                )

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.database = options["database"]

        self.remove_collections()
