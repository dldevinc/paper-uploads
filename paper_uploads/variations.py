import posixpath
from typing import Any, Dict, Iterable, Set, Union

from variations.variation import Variation

ALLOWED_VERSIONS = {'webp', '2x', '3x', '4x'}


class PaperVariation(Variation):
    """
    Расширение возможностей вариации.
      * Хранение имени вариации
      * Хранение настроек постобработки
      * Хранение перечня дополнительных версий вариации
    """

    def __init__(
        self,
        *args,
        name: str = '',
        postprocess: Union[Dict, bool, None] = None,
        versions: Iterable[str] = None,
        **kwargs
    ):
        self.name = name
        self.versions = versions or set()
        self.postprocess = postprocess
        super().__init__(*args, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise TypeError(value)
        self._name = value

    @property
    def postprocess(self) -> Union[Dict[str, Any], bool, None]:
        return self._postprocess

    @postprocess.setter
    def postprocess(self, value: Union[Dict[str, Any], bool, None]):
        if value is None or value is False:
            self._postprocess = value
        elif isinstance(value, dict):
            # lowercase format names
            self._postprocess = {k.lower(): v for k, v in value.items()}
        else:
            raise TypeError(value)

    @property
    def versions(self) -> Set:
        return self._versions

    @versions.setter
    def versions(self, value: Iterable[str]):
        self._versions = set(v.lower() for v in value)
        unknown_versions = self._versions.difference(ALLOWED_VERSIONS)
        if unknown_versions:
            raise ValueError('unknown versions: {}'.format(', '.join(unknown_versions)))

    def get_output_filename(self, input_filename: str) -> str:
        """
        Конструирует имя файла для вариации по имени файла исходника.
        Имя файла может включать путь — он остается неизменным.
        """
        if not self.name:
            raise RuntimeError('`name` is empty')

        dir_name, file_name = posixpath.split(input_filename)
        file_root, file_ext = posixpath.splitext(file_name)
        new_file_root = posixpath.extsep.join((file_root, self.name))
        file_name = ''.join((new_file_root, file_ext))
        name = posixpath.join(dir_name, file_name)
        return self.replace_extension(name)

    def get_postprocess_options(self, format: str) -> Union[Dict[str, Any], bool, None]:
        """
        Получение настроек постобработки для указанного формата
        """
        postprocess = self.postprocess
        if isinstance(postprocess, dict):
            return postprocess.get(format.lower())
        return postprocess
