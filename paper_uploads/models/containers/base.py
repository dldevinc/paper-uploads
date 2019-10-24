from django.core.files import File


class ContainerMixinBase:
    def attach_file(self, file: File):
        self._attach_file(file)
        self._post_attach_file()

    def _attach_file(self, file: File):
        raise NotImplementedError

    def _post_attach_file(self):
        pass

    def rename_file(self, new_name):
        raise NotImplementedError

    def delete_file(self):
        self._pre_delete_file()
        self._delete_file()

    def _delete_file(self):
        raise NotImplementedError

    def _pre_delete_file(self):
        pass

    def get_file_name(self) -> str:
        raise NotImplementedError

    def get_file_size(self) -> int:
        raise NotImplementedError

    def get_file_url(self) -> str:
        raise NotImplementedError

    def file_exists(self) -> bool:
        raise NotImplementedError
