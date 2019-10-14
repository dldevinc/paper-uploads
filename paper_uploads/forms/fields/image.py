from .base import FileFieldBase
from ..widgets import ImageWidget


class ImageField(FileFieldBase):
    widget = ImageWidget
