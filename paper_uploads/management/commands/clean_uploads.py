from django.apps import apps
from django.db import models
from django.core.management import BaseCommand
from django.utils.timezone import now, timedelta
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, DEFAULT_DB_ALIAS
from ...models import UploadedFile, UploadedImage, CollectionItemBase, CollectionBase


class Command(BaseCommand):
    verbosity = None
    database = DEFAULT_DB_ALIAS
    interactive = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--since', '-s', type=int, default=30,
            help='Minimum instance age in minutes to look for'
        )
        parser.add_argument(
            '--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
            help='Nominates the database to use. Defaults to the "default" database.',
        )
        parser.add_argument(
            '--noinput', '--no-input', action='store_false', dest='interactive',
            help='Do NOT prompt the user for input of any kind.'
        )

    @staticmethod
    def search_fields(related_model):
        """
        Поиск моделей и полей, ссылающихся на заданную.

        :type related_model: type
        :rtype: list of (models.Model, list)
        """
        for model in apps.get_models():
            if not model._meta.managed or model._meta.proxy:
                continue

            fields = []
            for field in model._meta.get_fields():
                if not field.concrete:
                    continue

                if not field.is_relation:
                    continue

                if issubclass(field.related_model, related_model):
                    fields.append(field)

            if fields:
                yield model, fields

    def get_used_ids(self, related_model, exclude_models=None):
        used_ids = set()
        for model, fields in self.search_fields(related_model):
            if exclude_models and issubclass(model, exclude_models):
                continue

            with transaction.atomic(self.database):
                # db_cursor = connections[self.database].cursor()
                # db_cursor.execute('LOCK TABLE %s IN ACCESS SHARE MODE' % model._meta.db_table)

                for field in fields:
                    used_values = model._base_manager.using(self.database).exclude(
                        models.Q((field.name, None))
                    ).values_list(
                        field.name,
                        flat=True
                    )
                    used_ids.update(used_values)
        return used_ids

    def clean_model(self, queryset, exclude_models=None):
        """
        Поиск экземпляров, на которые нет ссылок с других моделей.
        """
        related_model = queryset.model
        used_ids = self.get_used_ids(related_model, exclude_models)
        unused_qs = queryset.exclude(pk__in=used_ids)
        unused_count = unused_qs.count()
        if not unused_count:
            if self.verbosity >= 2:
                self.stderr.write(
                    self.style.NOTICE(
                        "There are no unused instances of {}".format(related_model.__name__)
                    )
                )
            return

        if self.interactive:
            while True:
                answer = input(
                    'Found \033[92m%d unused %s\033[0m objects. '
                    'What would you like to do with them?\n'
                    '(p)rint / (k)eep / (d)elete [default=keep]? ' % (
                        unused_count,
                        related_model.__name__
                    )
                )
                answer = answer.lower() or 'k'
                if answer in {'p', 'print'}:
                    self.stdout.write('\n')
                    qs = unused_qs.order_by('pk').only('file')
                    for index, item in enumerate(qs, start=1):
                        self.stdout.write('  {}) #{} (File: {})'.format(index, item.pk, item.file))
                    self.stdout.write('\n')
                elif answer in {'k', 'keep'}:
                    return
                elif answer in {'d', 'delete'}:
                    unused_qs.delete()
                    return

    def clean_source_missing(self, queryset, file_field='file'):
        """
        Поиск файлов
        """
        sourceless_items = set()
        related_model = queryset.model
        for instance in queryset.iterator():
            file = getattr(instance, file_field)
            if not file.storage.exists(file.name):
                sourceless_items.add(instance.pk)

        if not sourceless_items:
            if self.verbosity >= 2:
                self.stderr.write(
                    self.style.NOTICE(
                        "There are no instances of {} which have no source file.".format(related_model.__name__)
                    )
                )
            return

        if self.interactive:
            while True:
                answer = input(
                    'Found \033[92m%d %s\033[0m objects which are linked to a non-existent files.\n'
                    'What would you like to do with them?\n'
                    '(p)rint / (k)eep / (d)elete [default=keep]? ' % (
                        len(sourceless_items),
                        related_model.__name__
                    )
                )
                answer = answer.lower() or 'k'
                if answer in {'p', 'print'}:
                    self.stdout.write('\n')
                    qs = queryset.filter(pk__in=sourceless_items).order_by('pk').only('file')
                    for index, item in enumerate(qs, start=1):
                        self.stdout.write('  {}) #{} (File: {})'.format(index, item.pk, item.file.name))
                    self.stdout.write('\n')
                elif answer in {'k', 'keep'}:
                    return
                elif answer in {'d', 'delete'}:
                    queryset.filter(pk__in=sourceless_items).delete()
                    return

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.database = options['database']
        self.interactive = options['interactive']

        since = now() - timedelta(minutes=options['since'])
        self.clean_source_missing(UploadedFile._base_manager.using(self.database).all())
        self.clean_model(
            UploadedFile._base_manager.using(self.database).filter(
                uploaded_at__lte=since
            )
        )

        self.clean_source_missing(UploadedImage._base_manager.using(self.database).all())
        self.clean_model(
            UploadedImage._base_manager.using(self.database).filter(
                uploaded_at__lte=since
            )
        )

        for model in apps.get_models():
            if issubclass(model, CollectionItemBase) and model is not CollectionItemBase and not model._meta.abstract:
                self.clean_source_missing(
                    model._base_manager.using(self.database).non_polymorphic()
                )

        # Do not touch fresh galleries - they may not be saved yet.
        for model in apps.get_models():
            if issubclass(model, CollectionBase) and not model._meta.abstract:
                content_type = ContentType.objects.get_for_model(model, for_concrete_model=False)
                collection_qs = model._base_manager.using(self.database).filter(
                    collection_content_type=content_type,
                    created_at__lte=since
                )
                self.clean_model(collection_qs)