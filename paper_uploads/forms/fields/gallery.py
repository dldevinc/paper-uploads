from .base import FileFieldBase
from ..widgets import GalleryWidget


class GalleryField(FileFieldBase):
    widget = GalleryWidget
