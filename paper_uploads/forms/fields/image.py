from ..widgets import ImageWidget
from .base import FileFieldBase


class ImageField(FileFieldBase):
    widget = ImageWidget
