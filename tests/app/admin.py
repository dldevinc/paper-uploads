from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from paper_uploads.admin.file import UploadedFileAdmin
from paper_uploads.admin.image import UploadedImageAdmin

from .models import (
    CloudinaryCollectionFieldObject,
    CloudinaryFileExample,
    CloudinaryImageExample,
    CloudinaryMediaExample,
    CollectionFieldObject,
    CustomUploadedFile,
    CustomUploadedImage,
    FileFieldObject,
    ImageFieldObject,
)


@admin.register(CustomUploadedFile)
class CustomUploadedFileAdmin(UploadedFileAdmin):
    pass


@admin.register(CustomUploadedImage)
class CustomUploadedImageAdmin(UploadedImageAdmin):
    pass


@admin.register(FileFieldObject)
class FileFieldObjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "name", "file_required", "file", "file_custom_proxy", "file_custom"
            ),
        }),
        (_("Validators"), {
            "fields": (
                "file_extensions", "file_mimetypes", "file_size"
            ),
        }),
    )


@admin.register(ImageFieldObject)
class ImageFieldObjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "name", "image_required", "image", "image_custom_proxy", "image_custom"
            ),
        }),
        (_("Validators"), {
            "fields": (
                "image_extensions", "image_mimetypes", "image_size",
                "image_min_size", "image_max_size"
            ),
        }),
    )


@admin.register(CollectionFieldObject)
class CollectionFieldObjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "name",
            ),
        }),
        (None, {
            "fields": (
                "file_collection",
                "image_collection",
                "full_collection",
                "custom_proxy_collection",
                "custom_collection",
            ),
        }),
    )


@admin.register(CloudinaryFileExample)
class CloudinaryFileExampleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "name", "file_required", "file", "file_custom"
            ),
        }),
        (_("Validators"), {
            "fields": (
                "file_extensions", "file_mimetypes", "file_size"
            ),
        }),
    )


@admin.register(CloudinaryImageExample)
class CloudinaryImageExampleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "image", "image_public"
            ),
        }),
    )


@admin.register(CloudinaryMediaExample)
class CloudinaryMediaExampleAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "media",
            ),
        }),
    )


@admin.register(CloudinaryCollectionFieldObject)
class CloudinaryCollectionFieldObjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "file_collection", "image_collection", "media_collection", "full_collection",
                "custom_collection"
            ),
        }),
    )
