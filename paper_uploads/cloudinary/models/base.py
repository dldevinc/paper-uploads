from django.core.files import File
from ..container import CloudinaryContainerMixin


class CloudinaryFieldMixin(CloudinaryContainerMixin):
    def attach_file(self, file: File, **options):
        # set cloudinary options from field data
        owner_field = self.get_owner_field()
        if owner_field is not None:
            options.setdefault('cloudinary', owner_field.cloudinary_options)

        super().attach_file(file, **options)
