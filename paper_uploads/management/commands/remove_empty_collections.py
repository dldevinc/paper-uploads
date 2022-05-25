from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from .. import helpers


class Command(BaseCommand):
    help = """
    Удаление экземпляров коллекций, в которых нет ни одного элемента.
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
            "--min-age",
            type=int,
            default=24 * 3600,
            help="Minimum instance age in seconds to look for",
        )

    def handle(self, *args, **options):
        helpers.remove_empty_collections(
            min_age=options["min_age"],
            database=options["database"]
        )
