# Change Log

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
