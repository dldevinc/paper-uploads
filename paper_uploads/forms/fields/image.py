from ..widgets import ImageWidget
from .base import FileResourceFieldBase


class ImageField(FileResourceFieldBase):
    widget = ImageWidget
