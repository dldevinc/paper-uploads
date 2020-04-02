from ..widgets import CollectionWidget
from .base import FileFieldBase


class CollectionField(FileFieldBase):
    widget = CollectionWidget
