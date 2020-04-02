from django.utils.functional import LazyObject

from .conf import settings


class UploadStorage(LazyObject):
    def _setup(self):
        options = {
            key.lower(): value for key, value in settings.STORAGE_OPTIONS.items()
        }
        self._wrapped = settings.STORAGE(**options)


upload_storage = UploadStorage()
