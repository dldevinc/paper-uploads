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
 │    │    ┌────────────────────┐   ┌────────────────┐
 │    ├────►  UploadedFileBase  ├───►  UploadedFile  │
 │    │    └────────────────────┘   └────────────────┘
 │    │
 │    │    ┌─────────────────────┐   ┌─────────────────┐
 │    ├────►  UploadedImageBase  ├───►  UploadedImage  │
 │    │    └─────────────────────┘   └─────────────────┘
 │    │
 │    │    ┌──────────────────────────┐
 │    └────►  CollectionFileItemBase  │
 │         └┬─────────────────────────┘
 │          │
 │          │   ┌────────────────┐    ┌────────────┐
 │          ├───►  FileItemBase  ├───►  FileItem   │
 │          │   └────────────────┘    └────────────┘
 │          │
 │          │   ┌───────────────┐    ┌───────────┐
 │          ├───►  SVGItemBase  ├───►  SVGItem   │
 │          │   └───────────────┘    └───────────┘
 │          │
 │          │   ┌─────────────────┐    ┌─────────────┐
 │          └───►  ImageItemBase  ├───►  ImageItem   │
 │             └──────────────────┘    └─────────────┘
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
       │   ┌──────────────────────────┐   ┌──────────────────────┐
       ├───►  CloudinaryFileItemBase  ├───►  CloudinaryFileItem  │
       │   └──────────────────────────┘   └──────────────────────┘
       │
       │   ┌───────────────────────────┐   ┌───────────────────────┐
       ├───►  CloudinaryImageItemBase  ├───►  CloudinaryImageItem  │
       │   └───────────────────────────┘   └───────────────────────┘
       │
       │   ┌───────────────────────────┐   ┌───────────────────────┐
       └───►  CloudinaryMediaItemBase  ├───►  CloudinaryMediaItem  │
           └───────────────────────────┘   └───────────────────────┘
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
from .fields import CollectionField, CollectionItem, FileField, ImageField
from .file import UploadedFileBase, UploadedFile
from .image import UploadedImageBase, UploadedImage

__all__ = [
    "UploadedFileBase",
    "UploadedFile",
    "UploadedImageBase",
    "UploadedImage",
    "FileField",
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
