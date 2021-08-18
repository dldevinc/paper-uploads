import posixpath

from variations.variation import Variation


class PaperVariation(Variation):
    """
    Расширение возможностей вариации:
      * Хранение имени вариации
    """

    def __init__(self, *args, name: str = "", **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise TypeError(value)
        self._name = value

    def get_output_filename(self, input_filename: str) -> str:
        """
        Конструирует имя файла для вариации по имени файла исходника.
        Имя файла может включать путь — он остается неизменным.
        """
        if not self.name:
            raise RuntimeError("`name` is empty")

        dir_name, file_name = posixpath.split(input_filename)
        file_root, file_ext = posixpath.splitext(file_name)
        new_file_root = posixpath.extsep.join((file_root, self.name))
        file_name = "".join((new_file_root, file_ext))
        name = posixpath.join(dir_name, file_name)
        return self.replace_extension(name)
