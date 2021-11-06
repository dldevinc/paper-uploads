# Change Log

## [0.6.3](https://github.com/dldevinc/paper-uploads/tree/v0.6.3) - 2021-11-06
### Features
- Add abstract base classes for collection items. 
### Bug Fixes
- Fixed image recut with `python-rq`.
- Fixed `RecursionError` when deleting a collection.

## [0.6.2](https://github.com/dldevinc/paper-uploads/tree/v0.6.2) - 2021-11-02
### Features
- New `remove_empty_collections` management command.
### Bug Fixes
- Support explicit cascading deletion with `FileField` and `ImageField`.

## [0.6.1](https://github.com/dldevinc/paper-uploads/tree/v0.6.1) - 2021-10-20
### Features
- Add an ability to override admin model's views.

## [0.6.0](https://github.com/dldevinc/paper-uploads/tree/v0.6.0) - 2021-09-10
### ⚠ BREAKING CHANGES
- Removed `CloudinaryCollection` class.
### Features
- Add a method `get_file_folder` returning storage directory.
  Override this method to customize the upload folder.
### Bug Fixes
- Fix `RecursionError` when deleting ImageCollection.

## [0.5.2](https://github.com/dldevinc/paper-uploads/tree/v0.5.2) - 2021-09-03
### Bug Fixes
- Scale `max_width` and `max_height` for Retina versions.

## [0.5.1](https://github.com/dldevinc/paper-uploads/tree/v0.5.1) - 2021-08-25
### Features
- Make it possible to rename files with the same name.
- Add an ability to override `type` and `resource_type` options for Cloudinary fields.
- Switch from Travis CI to GitHub Actions.
- Update npm dependencies.

## [0.5.0](https://github.com/dldevinc/paper-uploads/tree/v0.5.0) - 2021-07-10
### ⚠ BREAKING CHANGES
- Drop support for Django versions before 2.2.
- Requires `paper-admin` >= 3.0.
- Migrate from `fine-uploader` to `dropzone.js`.
- Removed default permissions from all Django models.
- Collection previews has been reduced from `192x148` to `180x135`.
### Features
- Added Python 3.9 support.
- Added `remove_variations` management command.
- The `recreate_variations` management command has been completely rewritten.

## [0.4.5](https://github.com/dldevinc/paper-uploads/tree/v0.4.5) - 2020-10-26
- Add `cloudinary/helpers.py` file

## [0.4.4](https://github.com/dldevinc/paper-uploads/tree/v0.4.4) - 2020-10-19
- Fix missing templates

## [0.4.3](https://github.com/dldevinc/paper-uploads/tree/v0.4.3) - 2020-10-19
- Fix model checks

## [0.4.2](https://github.com/dldevinc/paper-uploads/tree/v0.4.2) - 2020-10-19
- Fix missing static files

## [0.4.0](https://github.com/dldevinc/paper-uploads/tree/v0.4.0) - 2020-09-04
- **Rewritten from scratch**
- Added `CLOUDINARY_TYPE` setting
- Added `CLOUDINARY_TEMP_DIR` setting
- Rename `CLOUDINARY` setting to `CLOUDINARY_UPLOADER_OPTIONS`
- Rename `ItemField` to `CollectionItem`
- Rename `MimetypeValidator` to `MimeTypeValidator`
- Signal `variation_created` was added
- Migrate to DropBox's checksum realization
- Remove postprocessing
- Upgrade development environment
