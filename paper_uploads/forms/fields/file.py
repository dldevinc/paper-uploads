from ..widgets import FileWidget
from .base import FileResourceFieldBase


class FileField(FileResourceFieldBase):
    widget = FileWidget
