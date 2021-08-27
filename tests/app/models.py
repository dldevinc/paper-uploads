import io
from typing import Dict
from urllib.parse import quote

from django.core.files import File
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from paper_uploads import helpers
from paper_uploads.cloudinary.models import *
from paper_uploads.models import *
from paper_uploads.models.base import *
from paper_uploads.typing import *
from paper_uploads.validators import *
from paper_uploads.variations import PaperVariation


class DummyResource(Resource):
    pass


class DummyFileResource(FileResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__filename = '{}.{}'.format(self.basename, self.extension)

    def get_file(self) -> File:
        file = getattr(self, '_file_cache', None)
        if file is None:
            buffer = io.BytesIO()
            buffer.write(b'This is example file content')
            buffer.seek(0)
            file = self._file_cache = File(buffer, name=self.basename)
        return file

    @property
    def name(self) -> str:
        return self.__filename

    def get_file_field(self) -> models.FileField:
        return models.Field(name='file')

    def get_file_size(self) -> int:
        return 28

    def get_file_url(self):
        return 'http://example.com/{}'.format(quote(self.get_basename()))

    def file_exists(self) -> bool:
        return True

    def _attach_file(self, file: File, **options):
        self.__filename = file.name
        self.basename = helpers.get_filename(file.name)
        self.extension = helpers.get_extension(file.name)
        return {
            'success': True,
        }

    def _rename_file(self, new_name: str, **options):
        self.__filename = new_name
        self.basename = helpers.get_filename(new_name)
        self.extension = helpers.get_extension(new_name)
        return {
            'success': True,
        }

    def _delete_file(self, **options):
        return {
            'success': True,
        }


class DummyFileFieldResource(FileFieldResource):
    file = models.FileField(_("file"), upload_to="file_field")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__name = "File_ABCD.jpg"

    def get_file(self) -> FieldFile:
        return self.file

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("file")


class DummyImageFieldResource(ImageFileResourceMixin, FileFieldResource):
    image = models.FileField(_("file"), upload_to="image_field")

    def get_file(self) -> FieldFile:
        return self.image

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("image")

    def get_variations(self) -> Dict[str, PaperVariation]:
        variations = getattr(self, "_variations", None)
        if variations is None:
            variations = self._variations = {
                "desktop": PaperVariation(
                    name="desktop",
                    size=(800, 0),
                    clip=False
                ),
            }
        return variations


class DummyVersatileImageResource(VersatileImageResourceMixin, FileFieldResource):
    file = models.FileField(_("file"), upload_to="versatile_image")

    def get_file(self) -> FieldFile:
        return self.file

    def get_file_field(self) -> models.FileField:
        return self._meta.get_field("file")

    def get_variations(self) -> Dict[str, PaperVariation]:
        return {
            "desktop": PaperVariation(
                name="desktop",
                size=(800, 0),
                clip=False
            ),
            "mobile": PaperVariation(
                name="mobile",
                size=(0, 600),
                clip=False
            ),
        }


class FileExample(models.Model):
    file = FileField(_("file"))


class ImageExample(models.Model):
    image = ImageField(_("image"), variations=dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
    ))


class FileCollection(Collection):
    file = CollectionItem(FileItem)


class PhotoCollection(ImageCollection):
    pass


class IsolatedFileCollection(Collection):
    file = CollectionItem(FileItem)

    class Meta:
        proxy = False


class ChildFileCollection(IsolatedFileCollection):
    file = None
    image = CollectionItem(ImageItem)
    svg = CollectionItem(SVGItem)


class CompleteCollection(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)

    VARIATIONS = dict(
        desktop=dict(
            size=(800, 0),
            clip=False
        ),
        mobile=dict(
            size=(0, 600),
            clip=False
        ),
    )


# ======================================================================================


class FileFieldObject(models.Model):
    name = models.CharField(_("name"), max_length=128)

    file = FileField(_("file"), blank=True)
    file_required = FileField(_("required file"))

    file_extensions = FileField(
        _("Extension"),
        blank=True,
        validators=[
            ExtensionValidator([".pdf", ".txt", ".doc"])
        ],
        help_text=_("Only `pdf`, `txt` and `doc` allowed")
    )
    file_mimetypes = FileField(
        _("MimeType"),
        blank=True,
        validators=[
            MimeTypeValidator(["image/svg+xml", "image/gif"])
        ],
        help_text=_("Only `image/svg+xml` and `image/gif` allowed")
    )
    file_size = FileField(
        _("Size"),
        blank=True,
        validators=[
            SizeValidator("16kb")
        ],
        help_text=_("Maximum file size is 16Kb")
    )

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")

    def __str__(self):
        return self.name


class ImageFieldObject(models.Model):
    name = models.CharField(_("name"), max_length=128)

    image = ImageField(_("image"), blank=True)
    image_required = ImageField(
        _("required image"),
        variations=dict(
            desktop=dict(
                name="desktop",
                size=(800, 0),
                clip=False
            ),
            mobile=dict(
                name="mobile",
                size=(0, 600),
                clip=False
            ),
        )
    )

    image_extensions = ImageField(
        _("Extension"),
        blank=True,
        validators=[
            ExtensionValidator([".png", ".gif"])
        ],
        help_text=_("Only `png` and `gif` allowed")
    )
    image_mimetypes = ImageField(
        _("MimeType"),
        blank=True,
        validators=[
            MimeTypeValidator(["image/png", "image/jpeg"])
        ],
        help_text=_("Only `image/png` and `image/jpeg` allowed")
    )
    image_size = ImageField(
        _("Size"),
        blank=True,
        validators=[
            SizeValidator("64kb")
        ],
        help_text=_("Maximum file size is 64Kb")
    )
    image_min_size = ImageField(
        _("Min size"),
        blank=True,
        validators=[
            ImageMinSizeValidator(640, 480)
        ],
        help_text=_("Image should be at least 640x480 pixels")
    )
    image_max_size = ImageField(
        _("Max size"),
        blank=True,
        validators=[
            ImageMaxSizeValidator(1024, 768)
        ],
        help_text=_("Image should be at most 1024x768 pixels")
    )

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")

    def __str__(self):
        return self.name


class CollectionFieldObject(models.Model):
    file_collection = CollectionField(FileCollection)
    image_collection = CollectionField(PhotoCollection)
    full_collection = CollectionField(CompleteCollection)

    class Meta:
        verbose_name = _("Collection")
        verbose_name_plural = _("Collections")

    def __str__(self):
        return "CollectionObject"


# ======================================================================================


class CloudinaryFileExample(models.Model):
    name = models.CharField(_("name"), max_length=128)

    file = CloudinaryFileField(_("file"), blank=True)
    file_required = CloudinaryFileField(_("required file"))

    file_extensions = CloudinaryFileField(
        _("Extension"),
        blank=True,
        validators=[
            ExtensionValidator([".pdf", ".txt", ".doc"])
        ],
        help_text=_("Only `pdf`, `txt` and `doc` allowed")
    )
    file_mimetypes = CloudinaryFileField(
        _("MimeType"),
        blank=True,
        validators=[
            MimeTypeValidator(["image/svg+xml", "image/gif"])
        ],
        help_text=_("Only `image/svg+xml` and `image/gif` allowed")
    )
    file_size = CloudinaryFileField(
        _("Size"),
        blank=True,
        validators=[
            SizeValidator("16kb")
        ],
        help_text=_("Maximum file size is 16Kb")
    )

    class Meta:
        verbose_name = _("Cloudinary File")
        verbose_name_plural = _("Cloudinary Files")

    def __str__(self):
        return self.name


class CloudinaryImageExample(models.Model):
    image = CloudinaryImageField(_("image"))
    image_public = CloudinaryImageField(
        _("Public image"),
        blank=True,
        cloudinary={
            "type": "upload",
            "folder": "page/images/%Y-%m-%d",
        }
    )

    class Meta:
        verbose_name = _("Cloudinary Image")
        verbose_name_plural = _("Cloudinary Images")

    def __str__(self):
        if self.image:
            return self.image.name
        else:
            return "ImageObject"


class CloudinaryMediaExample(models.Model):
    media = CloudinaryMediaField(_("media"))

    class Meta:
        verbose_name = _("Cloudinary Media")
        verbose_name_plural = _("Cloudinary Media")

    def __str__(self):
        if self.media:
            return self.media.name
        else:
            return "MediaObject"


class CloudinaryFileCollection(Collection):
    file = CollectionItem(CloudinaryFileItem)


class CloudinaryPhotoCollection(CloudinaryImageCollection):
    pass


class CloudinaryMediaCollection(Collection):
    media = CollectionItem(CloudinaryMediaItem)


class CloudinaryCompleteCollection(CloudinaryCollection):
    pass


class CloudinaryCollectionFieldObject(models.Model):
    file_collection = CollectionField(CloudinaryFileCollection)
    image_collection = CollectionField(CloudinaryPhotoCollection)
    media_collection = CollectionField(CloudinaryMediaCollection)
    full_collection = CollectionField(CloudinaryCompleteCollection)

    class Meta:
        verbose_name = _("Cloudinary Collection")
        verbose_name_plural = _("Cloudinary Collections")

    def __str__(self):
        return "CloudinaryCollectionObject"
