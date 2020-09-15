from ..widgets import CollectionWidget
from .base import FileResourceFieldBase


class CollectionField(FileResourceFieldBase):
    widget = CollectionWidget
