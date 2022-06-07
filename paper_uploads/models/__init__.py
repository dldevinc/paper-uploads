"""
Class hierarchy:

┌────────────────┐
│  ResourceBase  │
└┬───────────────┘
 │
┌▼───────────┐
│  Resource  │
└┬───────────┘
 │
┌▼───────────────┐
│  FileResource  │
└┬───────────────┘
 │
 │   ┌─────────────────────┐
 └───►  FileFieldResource  │
     └┬────────────────────┘
      │
      │    ┌────────────────────┐   ┌────────────────┐
      ├────►  UploadedFileBase  ├───►  UploadedFile  │
      │    └────────────────────┘   └────────────────┘
      │
      │    ┌───────────────────────┐   ┌───────────────────┐
      ├────►  UploadedSVGFileBase  ├───►  UploadedSVGFile  │
      │    └───────────────────────┘   └───────────────────┘
      │
      │    ┌─────────────────────┐   ┌─────────────────┐
      ├────►  UploadedImageBase  ├───►  UploadedImage  │
      │    └─────────────────────┘   └─────────────────┘
      │
      │    ┌──────────────────────────┐
      └────►  CollectionFileItemBase  │
           └┬─────────────────────────┘
            │
            │   ┌────────────────┐    ┌────────────┐
            ├───►  FileItemBase  ├───►  FileItem   │
            │   └────────────────┘    └────────────┘
            │
            │   ┌───────────────┐    ┌───────────┐
            ├───►  SVGItemBase  ├───►  SVGItem   │
            │   └───────────────┘    └───────────┘
            │
            │   ┌─────────────────┐    ┌─────────────┐
            └───►  ImageItemBase  ├───►  ImageItem   │
               └──────────────────┘    └─────────────┘
"""

from .collection import (
    Collection,
    CollectionItemBase,
    ImageCollection,
    FileItemBase,
    ImageItemBase,
    SVGItemBase,
    FileItem,
    ImageItem,
    SVGItem,
)
from .fields import CollectionField, CollectionItem, FileField, SVGFileField, ImageField
from .file import UploadedFileBase, UploadedFile
from .svg import UploadedSVGFileBase, UploadedSVGFile
from .image import UploadedImageBase, UploadedImage

__all__ = [
    "UploadedFileBase",
    "UploadedFile",
    "UploadedSVGFileBase",
    "UploadedSVGFile",
    "UploadedImageBase",
    "UploadedImage",
    "FileField",
    "SVGFileField",
    "ImageField",
    "CollectionField",
    "CollectionItemBase",
    "CollectionItem",
    "Collection",
    "ImageCollection",
    "FileItemBase",
    "SVGItemBase",
    "ImageItemBase",
    "FileItem",
    "SVGItem",
    "ImageItem",
]
