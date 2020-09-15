from django import forms


class FileResourceFieldBase(forms.ModelChoiceField):
    def __init__(
        self,
        *args,
        owner_app_label=None,
        owner_model_name=None,
        owner_fieldname=None,
        configuration=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.widget.owner_app_label = owner_app_label
        self.widget.owner_model_name = owner_model_name
        self.widget.owner_fieldname = owner_fieldname
        self.widget.configuration = configuration
