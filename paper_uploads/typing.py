from typing import IO, Any, Dict, Union

from django.core.files import File

__all__ = [
    'FileLike',
    'VariationConfig'
]

FileLike = Union[IO, File]
VariationConfig = Dict[str, Any]
