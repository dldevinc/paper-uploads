from django import forms
from django.utils.translation import gettext_lazy as _
from paper_admin.admin.renderers import PaperFormRenderer


class UploadedFileBaseForm(forms.ModelForm):
    default_renderer = PaperFormRenderer
    new_name = forms.CharField(required=True, label=_("File name"), max_length=255,)

    class Meta:
        fields = ("new_name",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["new_name"].initial = self.instance.basename

    def save(self, commit=True):
        old_name = self.instance.name
        new_name = self.cleaned_data["new_name"]
        if old_name != new_name:
            if self.instance.extension:
                new_name += "." + self.instance.extension
            self.instance.rename_file(new_name)
        return super().save(commit)
