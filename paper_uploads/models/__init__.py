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
    FileItem,
    FileItemBase,
    ImageCollection,
    ImageItem,
    ImageItemBase,
    SVGItem,
    SVGItemBase,
)
from .fields import CollectionField, CollectionItem, FileField, ImageField, SVGFileField
from .file import UploadedFile, UploadedFileBase
from .image import UploadedImage, UploadedImageBase
from .svg import UploadedSVGFile, UploadedSVGFileBase

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
