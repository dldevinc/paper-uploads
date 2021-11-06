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
    "FileItemBase",
    "SVGItemBase",
    "ImageItemBase",
    "FileItem",
    "SVGItem",
    "ImageItem",
]
