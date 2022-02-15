from ...models.mixins import FileProxyMixin


class ReadonlyCloudinaryFileProxyMixin(FileProxyMixin):
    """
    Проксирование некоторых свойств файла (только для чтения) на уровень модели

    TODO: удалить _require_file?
    """

    @property
    def url(self):
        self._require_file()  # noqa: F821
        return self.get_file().url  # noqa: F821
