import posixpath
from django import forms
from django.utils.translation import gettext_lazy as _
from paper_admin.renderer import PaperFormRenderer


class UploadedFileBaseForm(forms.ModelForm):
    default_renderer = PaperFormRenderer
    new_name = forms.CharField(
        required=True,
        label=_('File name'),
        max_length=255,
    )

    class Meta:
        fields = ('new_name', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['new_name'].initial = self.instance.name

    def save(self, commit=True):
        old_name = self.instance.name
        new_name = self.cleaned_data['new_name']
        if old_name != new_name:
            root, ext = posixpath.splitext(self.instance.file.name)
            name = ''.join((new_name, ext))
            with self.instance.file.open() as fp:
                self.instance.file.save(name, fp, save=False)
            self.instance.name = new_name
        return super().save(commit)
