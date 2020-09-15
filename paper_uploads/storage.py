from django.utils.functional import LazyObject

from .conf import settings
from .utils import lowercased_dict_keys


class UploadStorage(LazyObject):
    def _setup(self):
        options = lowercased_dict_keys(settings.STORAGE_OPTIONS)
        self._wrapped = settings.STORAGE(**options)


upload_storage = UploadStorage()
