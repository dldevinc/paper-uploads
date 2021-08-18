import os

from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from .variations import PaperVariation


class TemporaryUploadedFile(UploadedFile):
    """
    Обертка над файлом, удаляющая его при закрытии.

    В отличие от django.core.files.uploadedfile.TemporaryUploadedFile, не создает
    новый временный файл, а оборачивает уже существующий. Используется для передачи
    загруженного файла в функцию сохранения.
    """
    def close(self):
        super().close()
        try:
            os.unlink(self.file.name)
        except OSError:
            pass


class VariationFile(File):
    """
    Файл вариации изображения.
    """

    def __init__(self, instance, variation_name):
        self.instance = instance
        self.variation_name = variation_name
        self.storage = instance.get_file().storage
        filename = self.variation.get_output_filename(instance.name)
        super().__init__(None, filename)

    def __eq__(self, other):
        if hasattr(other, "name"):
            return self.name == other.name
        return self.name == other

    def __hash__(self):
        return hash(self.name)

    def _require_file(self):
        if not self:
            raise ValueError(
                _("Variation '%s' has no file associated with it.") % self.variation_name
            )

    def _get_file(self) -> File:
        self._require_file()
        if getattr(self, "_file", None) is None:
            self._file = self.storage.open(self.name, "rb")
        return self._file

    def _set_file(self, file: File):
        self._file = file

    def _del_file(self):
        del self._file

    file = property(_get_file, _set_file, _del_file)

    @property
    def variation(self) -> PaperVariation:
        variations = self.instance.get_variations()
        return variations[self.variation_name]

    @property
    def path(self) -> str:
        self._require_file()
        return self.storage.path(self.name)

    @property
    def url(self) -> str:
        self._require_file()
        return self.storage.url(self.name)

    @property
    def size(self) -> int:
        self._require_file()
        return self.storage.size(self.name)

    def exists(self) -> bool:
        if not self:
            return False
        return self.storage.exists(self.name)

    def open(self, mode: str = "rb"):
        self._require_file()
        if getattr(self, "_file", None) is None:
            self.file = self.storage.open(self.name, mode)
        else:
            self.file.open(mode)
        return self

    # open() doesn't alter the file's contents, but it does reset the pointer
    open.alters_data = True  # noqa

    def delete(self):
        if not self:
            return

        if hasattr(self, "_file"):
            self.close()
            del self.file

        self.storage.delete(self.name)
        self.name = None

    delete.alters_data = True

    @property
    def closed(self) -> bool:
        file = getattr(self, "_file", None)
        return file is None or file.closed

    def close(self):
        file = getattr(self, "_file", None)
        if file is not None:
            file.close()

    @property
    def width(self) -> int:
        return self._get_image_dimensions()[0]

    @property
    def height(self) -> int:
        return self._get_image_dimensions()[1]

    def _get_image_dimensions(self):
        if not hasattr(self, "_dimensions_cache"):
            dimensions = self.variation.get_output_size(
                (self.instance.width, self.instance.height)
            )
            self._dimensions_cache = dimensions
        return self._dimensions_cache
