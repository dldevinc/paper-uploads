from django.db.models.query import QuerySet
from polymorphic.managers import PolymorphicManager as DefaultPolymorphicManager
from polymorphic.query import PolymorphicQuerySet


class ResourceQuerysetMixin:
    @property
    def required_fields(self):
        return self.model._resource_meta.required_fields

    def only(self, *fields):
        new_fields = tuple(set(fields).union(self.required_fields))
        return super().only(*new_fields)

    def defer(self, *fields):
        new_fields = tuple(set(fields).difference(self.required_fields))
        return super().defer(*new_fields)


class ResourceQuerySet(ResourceQuerysetMixin, QuerySet):
    pass


class PolymorphicResourceQuerySet(ResourceQuerysetMixin, PolymorphicQuerySet):
    pass


class PolymorphicResourceManager(DefaultPolymorphicManager):
    queryset_class = PolymorphicResourceQuerySet


class ProxyPolymorphicManager(PolymorphicResourceManager):
    """
    Менеджер, удаляющий из SQL-запроса фильтрацию по полю
    polymorphic_ctype, чтобы выборка по классу прокси-модели
    могла возвращать экземпляры проксируемой модели.
    """
    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db, hints=self._hints)
