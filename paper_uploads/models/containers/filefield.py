import hashlib
from django.core.files import File
from .base import ContainerMixinBase


class FileFieldContainerMixin(ContainerMixinBase):
    def _attach_file(self, file: File):
        self.file.save(file.name, file, save=False)

    def rename_file(self, new_name):
        name = '.'.join((new_name, self.extension))
        with self.file.open() as fp:
            self.file.save(name, fp, save=False)

    def _delete_file(self):
        self.file.delete(save=False)

    def get_file_name(self) -> str:
        return self.file.name

    def get_file_size(self) -> int:
        return self.file.size

    def get_file_url(self) -> str:
        return self.file.url

    def file_exists(self) -> bool:
        return self.file.storage.exists(self.get_file_name())

    def get_file_hash(self) -> str:
        """
        Generate a SHA-1 hash from a file's contents
        """
        file_closed = self.file.closed
        sha1 = hashlib.sha1()
        for chunk in self.file.open():
            sha1.update(chunk)
        if file_closed:
            self.file.close()
        else:
            self.file.seek(0)
        return sha1.hexdigest()
