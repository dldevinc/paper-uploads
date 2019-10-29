from itertools import chain
from django.core import checks
from django.core.files import File


class ProxyAttributesContainerMixin:
    PROXY_FILE_ATTRIBUTES = {}

    def __getattr__(self, item):
        if item in self.PROXY_FILE_ATTRIBUTES:
            return getattr(self.file, item)
        return super().__getattr__(item)

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_prohibited_field_names(),
        ]

    @classmethod
    def _check_prohibited_field_names(cls, **kwargs):
        errors = []
        for field in chain(cls._meta.local_fields, cls._meta.local_many_to_many):
            if field.name in cls.PROXY_FILE_ATTRIBUTES:
                errors.append(
                    checks.Error(
                        "The field '%s' clashes with the proxied file attribute '%s'" % (
                            field.name, field.name
                        ),
                        obj=cls,
                        )
                )
        return errors


class ContainerMixinBase:
    def __getattr__(self, item):
        """
        Реализация метода по умолчанию. Делает возможным его последовательное
        расширение в классах-потомках.
        """
        raise AttributeError(
            "'%s' object has no attribute '%s'" % (self.__class__.__name__, item)
        )

    def attach_file(self, file: File, **options):
        data = self._attach_file(file, **options)
        self._post_attach_file(data)

    def _attach_file(self, file: File, **options):
        raise NotImplementedError

    def _post_attach_file(self, data=None):
        pass

    def rename_file(self, new_name: str):
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
