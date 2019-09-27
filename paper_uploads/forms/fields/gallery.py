from .base import FileFieldBase
from ..widgets import GalleryWidget


class CollectionField(FileFieldBase):
    widget = GalleryWidget
