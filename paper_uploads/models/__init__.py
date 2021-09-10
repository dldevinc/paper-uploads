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
 ├───►  FileFieldResource  │
 │   └┬────────────────────┘
 │    │
 │    │    ┌────────────────┐
 │    ├────►  UploadedFile  │
 │    │    └────────────────┘
 │    │
 │    │    ┌─────────────────┐
 │    ├────►  UploadedImage  │
 │    │    └─────────────────┘
 │    │
 │    │    ┌──────────────────────────┐
 │    └────►  CollectionFileItemBase  │
 │         └┬─────────────────────────┘
 │          │
 │          │   ┌────────────┐
 │          ├───►  FileItem  │
 │          │   └────────────┘
 │          │
 │          │   ┌───────────┐
 │          ├───►  SVGItem  │
 │          │   └───────────┘
 │          │
 │          │   ┌─────────────┐
 │          └───►  ImageItem  │
 │              └─────────────┘
 │
 │   ┌──────────────────────────┐
 └───►  CloudinaryFileResource  │
     └┬─────────────────────────┘
      │
      │    ┌──────────────────┐
      ├────►  CloudinaryFile  │
      │    └──────────────────┘
      │
      │    ┌───────────────────┐
      ├────►  CloudinaryImage  │
      │    └───────────────────┘
      │
      │    ┌───────────────────┐
      ├────►  CloudinaryMedia  │
      │    └───────────────────┘
      │
      │    ┌────────────────────────────────────┐
      └────►  CollectionCloudinaryFileItemBase  │
           └┬───────────────────────────────────┘
            │
            │   ┌──────────────────────┐
            ├───►  CloudinaryFileItem  │
            │   └──────────────────────┘
            │
            │   ┌───────────────────────┐
            ├───►  CloudinaryImageItem  │
            │   └───────────────────────┘
            │
            │   ┌───────────────────────┐
            └───►  CloudinaryMediaItem  │
                └───────────────────────┘
"""

from .collection import (
    Collection,
    CollectionItemBase,
    FileItem,
    ImageCollection,
    ImageItem,
    SVGItem,
)
from .fields import CollectionField, CollectionItem, FileField, ImageField
from .file import UploadedFile
from .image import UploadedImage

__all__ = [
    "UploadedFile",
    "UploadedImage",
    "FileField",
    "ImageField",
    "CollectionField",
    "CollectionItemBase",
    "CollectionItem",
    "Collection",
    "ImageCollection",
    "FileItem",
    "SVGItem",
    "ImageItem",
]
