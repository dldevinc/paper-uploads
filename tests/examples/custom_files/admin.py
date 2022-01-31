from django.contrib import admin

from paper_uploads.admin.file import UploadedFileAdminBase
from paper_uploads.admin.image import UploadedImageAdminBase

from .models import CustomUploadedFile, CustomUploadedImage, Page


@admin.register(CustomUploadedFile)
class CustomUploadedFileAdmin(UploadedFileAdminBase):
    pass


@admin.register(CustomUploadedImage)
class CustomUploadedImageAdmin(UploadedImageAdminBase):
    pass


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    pass
