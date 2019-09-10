from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from ...models import UploadedImageBase


class Command(BaseCommand):
    options = None
    verbosity = None
    database = DEFAULT_DB_ALIAS

    def add_arguments(self, parser):
        parser.add_argument(
            '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
            help='Nominates the database to use. Defaults to the "default" database.',
        )
        parser.add_argument(
            '--fix-missing', action='store_true', default=False,
            help='Recreate all missing variation files from source.',
        )

    def check_variations(self):
        for model in apps.get_models():
            if not issubclass(model, UploadedImageBase):
                continue

            for instance in model._meta.base_manager.using(self.database).all():
                missed_original = not instance.file.storage.exists(instance.file.name)
                missed_variations = []
                for vname, vfile in instance.get_variation_files():
                    if not vfile.exists():
                        missed_variations.append(vname)

                invalid = False
                recreatable = self.options['fix_missing'] and not missed_original
                message = "Errors were found in '{}.{}' #{}:".format(
                    model._meta.app_label,
                    model._meta.model_name,
                    instance.pk
                )

                if missed_original:
                    invalid = True
                    message += "\n  Not found source file"

                if missed_variations:
                    invalid = True
                    for vname in missed_variations:
                        message += "\n  Not found variation '{}'".format(vname)
                        if recreatable:
                            message += " (recreated)"

                    if recreatable:
                        instance.recut(names=missed_variations)

                if invalid:
                    self.stdout.write(
                        self.style.ERROR(message)
                    )

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options['verbosity']
        self.database = options['database']

        self.check_variations()
