from typing import Any, List

from django.core import checks
from django.db.models import Field
from django.utils.functional import cached_property

from ... import forms
from .base import FileFieldBase


class CollectionField(FileFieldBase):
    def __init__(self, to, **kwargs):
        kwargs['blank'] = True
        super().__init__(to=to, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'blank' in kwargs:
            del kwargs['blank']
        return name, path, args, kwargs

    def _check_relation_class(self):
        from ...models.collection import CollectionBase

        rel_is_string = isinstance(self.remote_field.model, str)
        if rel_is_string:
            return []

        model_name = (
            self.remote_field.model
            if rel_is_string
            else self.remote_field.model._meta.object_name
        )
        if not issubclass(self.remote_field.model, CollectionBase):
            return [
                checks.Error(
                    "Field defines a relation with model '%s', which is not "
                    "subclass of CollectionBase" % model_name,
                    obj=self,
                )
            ]
        return []

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.CollectionField,
            **kwargs
        })


class ItemField:
    """
    Поле для подключения классов элементов галереи.
    Допустимо для использования только в подклассах галерей.
    """

    default_validators = []     # type: List[Any]

    def __init__(self, to, name=None, validators=(), postprocess=None, options=None):
        self.name = name

        try:
            to._meta.model_name
        except AttributeError:
            assert isinstance(to, str), (
                "%s(%r) is invalid. First parameter to %s must be a model"
                % (self.__class__.__name__, to, self.__class__.__name__,)
            )

        self.model = to
        self.options = options or {}
        self.postprocess = postprocess
        self._validators = list(validators)

    def check(self, **kwargs):
        return [
            *Field._check_field_name(self, **kwargs),
            *Field._check_validators(self, **kwargs),
        ]

    @cached_property
    def validators(self):
        return [*self.default_validators, *self._validators]

    def contribute_to_class(self, cls, name, **kwargs):
        self.name = self.name or name
        item_types_attribute = '_{}__item_types'.format(cls.__name__)
        item_types = getattr(cls, item_types_attribute, None)
        if item_types is not None:
            item_types[self.name] = self
