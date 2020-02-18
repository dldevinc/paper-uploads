from ..widgets import FileWidget
from .base import FileFieldBase


class FileField(FileFieldBase):
    widget = FileWidget
