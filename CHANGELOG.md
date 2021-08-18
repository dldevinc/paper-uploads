# Change Log

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
