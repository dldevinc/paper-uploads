from .base import FileFieldBase
from ..widgets import CollectionWidget


class CollectionField(FileFieldBase):
    widget = CollectionWidget
