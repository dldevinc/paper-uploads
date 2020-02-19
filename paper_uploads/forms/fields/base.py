from django import forms


class FileFieldBase(forms.ModelChoiceField):
    def __init__(
        self,
        *args,
        owner_app_label=None,
        owner_model_name=None,
        owner_fieldname=None,
        validation=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.widget.owner_app_label = owner_app_label
        self.widget.owner_model_name = owner_model_name
        self.widget.owner_fieldname = owner_fieldname
        self.widget.validation = validation
