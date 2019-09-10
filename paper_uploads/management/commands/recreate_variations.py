from inspect import isclass
from django.db import models
from django.core.management import BaseCommand
from django.utils.module_loading import import_string
from django.db import DEFAULT_DB_ALIAS
from ...models import UploadedImageBase, Gallery


class Command(BaseCommand):
    """
    Пример:
        python3 manage.py recreate_variations blog.models.Page.image:desktop,mobile
    """
    verbosity = None
    database = DEFAULT_DB_ALIAS

    def add_arguments(self, parser):
        parser.add_argument(
            'fields_or_models', nargs='+',
            metavar='app_label.ModelName[.FieldName][:Variations]',
            help='Restricts recreated variations to the specified image fields, '
                 'gallery models and variation names.'
        )
        parser.add_argument(
            '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
            help='Nominates the database to use. Defaults to the "default" database.',
        )

    def process_path(self, path, variations):
        try:
            module = import_string(path)
        except ImportError:
            # try to check field path...
            model_path, fieldname = path.rsplit('.', 1)
            model = import_string(model_path)
            if isclass(model) and issubclass(model, models.Model):
                field = model._meta.get_field(fieldname)
                if not field.is_relation:
                    raise TypeError("field '%s' is not a relation field" % path)
                if not issubclass(field.related_model, UploadedImageBase):
                    raise TypeError("field '%s' refers to the non-image model" % path)

                # check variations
                if variations:
                    for name in variations:
                        if name not in field.variations:
                            raise TypeError("variation '%s' is undefined" % name)

                # recut field
                instances = model._meta.base_manager.exclude((fieldname, None))
                instance_count = instances.count()
                for index, instance in enumerate(instances, start=1):
                    if self.verbosity >= 1:
                        self.stdout.write(self.style.SUCCESS(
                            "\rRecreate variations '{}' ({}/{}) ... ".format(
                                path,
                                index,
                                instance_count
                            )
                        ), ending='')
                    field = getattr(instance, fieldname)
                    field.recut(names=variations)
                self.stdout.write('')
        else:
            # is it a gallery model?
            if issubclass(module, Gallery):
                # check variations
                if variations:
                    for name in variations:
                        if name not in module.VARIATIONS:
                            raise TypeError("variation '%s' is undefined" % name)

                if self.verbosity >= 1:
                    self.stdout.write(self.style.SUCCESS(
                        "Recreate variations '{}' ... ".format(
                            path
                        )
                    ))
                module.recut(names=variations)
            else:
                self.stderr.write(self.style.ERROR(
                    "Error: the model '%s' is not a subclass of Gallery" % path
                ))

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.database = options['database']

        for path in options['fields_or_models']:
            module_path, _, variations = path.partition(':')
            variations = tuple(map(str.strip, variations.split(',')))
            self.process_path(module_path, variations)
