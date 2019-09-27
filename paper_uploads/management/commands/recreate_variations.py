from django.apps import apps
from django.core.management import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from ...models import UploadedImageBase, Gallery


class Command(BaseCommand):
    verbosity = None
    database = DEFAULT_DB_ALIAS

    def add_arguments(self, parser):
        parser.add_argument(
            'model', metavar='app_label.ModelName',
            help='Specify the model to recreate variations for',
        )
        parser.add_argument(
            '--field', dest='field',
            help='Restricts recreated variations to the specified field',
        )
        parser.add_argument(
            '--variations', dest='variations', nargs='+',
            help='Specify the variation names to recreate variations for',
        )
        parser.add_argument(
            '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
            help='Nominates the database to use. Defaults to the "default" database.',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.database = options['database']

        model = apps.get_model(options['model'])
        fieldname = options['field']
        if fieldname:
            field = model._meta.get_field(fieldname)
            if not field.is_relation:
                raise TypeError("field '%s' is not a relation field" % fieldname)
            if not issubclass(field.related_model, UploadedImageBase):
                raise TypeError("field '%s' refers to the non-image model" % fieldname)
        else:
            field = None

        variations = options['variations']
        if issubclass(model, Gallery) and hasattr(model, 'VARIATIONS'):
            # recut collection
            if variations:
                for name in variations:
                    if name not in model.VARIATIONS:
                        raise TypeError("The requested variation '%s' does not exist" % name)

            total = model.objects.using(self.database).count()
            for index, collection in enumerate(model.objects.using(self.database).iterator(), start=1):     # use objects manager!
                if self.verbosity >= 1:
                    self.stdout.write(self.style.SUCCESS(
                        "Recreate variations '{}' #{} ({}/{}) ... ".format(options['model'], collection.pk, index, total)
                    ))
                collection.recut(names=variations, using=self.database)
        elif field is not None:
            # recut model field
            if variations:
                for name in variations:
                    if name not in field.variations:
                        raise TypeError("variation '%s' is undefined" % name)

            instances = model._base_manager.using(self.database).exclude((fieldname, None))
            total = instances.count()
            for index, instance in enumerate(instances, start=1):
                if self.verbosity >= 1:
                    self.stdout.write(self.style.SUCCESS(
                        "Recreate variations '{}' #{} ({}/{}) ... ".format(options['model'], instance.pk, index, total)
                    ), ending='\r')
                field = getattr(instance, fieldname)
                field.recut(names=variations)
            self.stdout.write('')
        else:
            raise RuntimeError('a field name must be specified for non-collection models')
