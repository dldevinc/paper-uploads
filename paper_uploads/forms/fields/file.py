from .base import FileFieldBase
from ..widgets import FileWidget


class FileField(FileFieldBase):
    widget = FileWidget
