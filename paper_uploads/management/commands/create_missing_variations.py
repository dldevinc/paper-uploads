from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from .. import helpers


class Command(BaseCommand):
    help = """
    Создаёт отсутствующие файлы вариаций.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help="Nominates the database to use. Defaults to the 'default' database.",
        )
        parser.add_argument(
            "--async",
            action="store_true",
            help="Use django-rq to create variation files",
        )

    def handle(self, *args, **options):
        helpers.create_missing_variations(
            async_=options["async"],
            database=options["database"]
        )
