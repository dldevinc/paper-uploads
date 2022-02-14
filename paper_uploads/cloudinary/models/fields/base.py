class CloudinaryOptionsMixin:
    def __init__(self, *args, upload_to="", cloudinary=None, **kwargs):
        self.cloudinary = cloudinary
        super().__init__(*args, upload_to=upload_to, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "cloudinary" in kwargs:
            del kwargs["cloudinary"]
        return name, path, args, kwargs
