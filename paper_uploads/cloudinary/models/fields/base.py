class CloudinaryOptionsMixin:
    def __init__(self, *args, cloudinary=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cloudinary = cloudinary

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "cloudinary" in kwargs:
            del kwargs["cloudinary"]
        return name, path, args, kwargs
