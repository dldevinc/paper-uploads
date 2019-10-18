import posixpath
from typing import Union, Dict
from variations.variation import Variation


class PaperVariation(Variation):
    """
    Расширение возможностей вариации.
      * Хранение имени вариации
      * Хранение настроек постобработки
    """
    def __init__(self, *args, name: str = '', postprocess: Union[Dict, bool] = None, **kwargs):
        self.name = name
        self.postprocess = postprocess
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise TypeError(value)
        self._name = value

    @property
    def postprocess(self) -> Union[Dict, bool, None]:
        return self._postprocess

    @postprocess.setter
    def postprocess(self, value):
        if value is None or value is False:
            self._postprocess = value
            return
        if isinstance(value, dict):
            # lowercase format names
            self._postprocess = {
                k.lower(): v
                for k, v in value.items()
            }
        else:
            raise TypeError(value)

    def get_output_filename(self, input_filename: str) -> str:
        """
        Конструирует имя файла для вариации по имени файла исходника.
        Имя файла может включать путь — он остается неизменным.
        """
        if not self.name:
            raise RuntimeError('variation `name` is empty')

        dir_name, file_name = posixpath.split(input_filename)
        file_root, file_ext = posixpath.splitext(file_name)
        new_file_root = posixpath.extsep.join((file_root, self.name))
        file_name = ''.join((new_file_root, file_ext))
        name = posixpath.join(dir_name, file_name)
        return self.replace_extension(name)

    def get_postprocess_options(self, format: str) -> Union[Dict, bool, None]:
        """
        Получение настроек постобработки для указанного формата
        """
        if self.postprocess is False:
            return False
        elif self.postprocess is not None:
            return self.postprocess.get(format.lower())
