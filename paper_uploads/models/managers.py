from django.db.models.manager import Manager
from polymorphic.managers import PolymorphicManager


class ResourceManagerMixin:
    @property
    def required_fields(self):
        return self.model._resource_meta.required_fields

    def only(self, *fields):
        new_fields = tuple(set(fields).union(self.required_fields))
        return super().only(*new_fields)

    def defer(self, *fields):
        new_fields = tuple(set(fields).difference(self.required_fields))
        return super().defer(*new_fields)


class ResourceManager(ResourceManagerMixin, Manager):
    pass


class PolymorphicResourceManager(ResourceManagerMixin, PolymorphicManager):
    pass
