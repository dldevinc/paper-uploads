from django.contrib import admin

from ..models.svg import UploadedSVGFile
from .file import UploadedFileAdmin


@admin.register(UploadedSVGFile)
class UploadedSVGFileAdmin(UploadedFileAdmin):
    pass
