from django import forms


class ResourceFieldBase(forms.ModelChoiceField):
    def __init__(
        self,
        *args,
        owner_app_label=None,
        owner_model_name=None,
        owner_fieldname=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.widget.owner_app_label = owner_app_label
        self.widget.owner_model_name = owner_model_name
        self.widget.owner_fieldname = owner_fieldname


class FileResourceFieldBase(ResourceFieldBase):
    def __init__(
        self,
        *args,
        configuration=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.widget.configuration = configuration
