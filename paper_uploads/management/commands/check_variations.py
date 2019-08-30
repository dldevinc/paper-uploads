from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from ...models import UploadedImageBase


class Command(BaseCommand):
    verbosity = None
    database = DEFAULT_DB_ALIAS
    help = 'Check if all variation files exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
            help='Nominates the database to use. Defaults to the "default" database.',
        )
        parser.add_argument(
            '--fix-missing', action='store_true', default=False,
            help='Create all missing variation files from source.',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.database = options['database']

        for model in apps.get_models():
            if not issubclass(model, UploadedImageBase):
                continue

            for instance in model._meta.base_manager.all():
                missed_original = not instance.file.storage.exists(instance.file.name)
                missed_variations = []
                for vname, vfile in instance.get_variation_files():
                    if not vfile.exists():
                        missed_variations.append(vname)

                message = "Error on '{}.{}' (#{})".format(
                    model._meta.app_label,
                    model._meta.model_name,
                    instance.pk
                )
                if missed_original:
                    self.stderr.write(
                        self.style.ERROR(
                            "{}:  Not found source file".format(message)
                        )
                    )
                if missed_variations:
                    for vname in missed_variations:
                        self.stderr.write(
                            self.style.WARNING(
                                "{}:  Not found variation: {}".format(message, vname)
                            )
                        )
                    if options['fix_missing'] and not missed_original:
                        instance.recut(names=missed_variations)
