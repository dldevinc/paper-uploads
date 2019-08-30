import posixpath
from django import forms
from paper_admin.renderer import PaperFormRenderer
from ..models import UploadedFile, UploadedImage, GalleryFileItem, GalleryImageItem


class FileEditForm(forms.ModelForm):
    default_renderer = PaperFormRenderer
    new_name = forms.CharField(
        required=True,
        label=UploadedFile._meta.get_field('name').verbose_name.capitalize(),
        help_text=UploadedFile._meta.get_field('name').help_text,
        max_length=UploadedFile._meta.get_field('name').max_length,
    )

    class Meta:
        model = UploadedFile
        fields = ('new_name', 'display_name', )

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


class ImageEditForm(FileEditForm):
    class Meta:
        model = UploadedImage
        fields = ('new_name', 'alt', 'title')


# ==============================================================================


class GalleryFileItemForm(FileEditForm):
    class Meta(FileEditForm.Meta):
        model = GalleryFileItem
        fields = ('new_name', )


class GalleryImageItemForm(ImageEditForm):
    class Meta(ImageEditForm.Meta):
        model = GalleryImageItem
        fields = ('new_name', 'alt', 'title')
