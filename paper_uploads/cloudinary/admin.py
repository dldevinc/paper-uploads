from django.contrib import admin

from ..admin.file import UploadedFileAdmin
from ..admin.image import UploadedImageAdmin
from .models import CloudinaryFile, CloudinaryImage, CloudinaryMedia

admin.register(CloudinaryFile)(UploadedFileAdmin)
admin.register(CloudinaryImage)(UploadedImageAdmin)
admin.register(CloudinaryMedia)(UploadedFileAdmin)
