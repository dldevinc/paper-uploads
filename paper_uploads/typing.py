from typing import IO, Any, Dict, List, Tuple, Union

from django.core.files import File

__all__ = ["FileLike", "Limitations", "VariationConfig"]

FileLike = Union[IO, File]
VariationConfig = Dict[str, Any]
Limitations = List[Union[str, Tuple[str, str]]]
