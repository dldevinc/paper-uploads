from django.core import checks
from .base import FileFieldBase
from ... import forms


class GalleryField(FileFieldBase):
    def __init__(self, to, **kwargs):
        kwargs['blank'] = True
        super().__init__(to=to, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'blank' in kwargs:
            del kwargs['blank']
        return name, path, args, kwargs

    def _check_relation_class(self):
        from ...models.gallery import GalleryBase

        rel_is_string = isinstance(self.remote_field.model, str)
        if rel_is_string:
            return []

        model_name = self.remote_field.model if rel_is_string else self.remote_field.model._meta.object_name
        if not issubclass(self.remote_field.model, GalleryBase):
            return [
                checks.Error(
                    "Field defines a relation with model '%s', which is not "
                    "subclass of GalleryBase" % model_name,
                    obj=self,
                )
            ]
        return []

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.GalleryField,
            'owner_app_label': self.opts.app_label.lower(),
            'owner_model_name': self.opts.model_name.lower(),
            'owner_fieldname': self.name,
            **kwargs
        })
