# Change Log

## [0.18.5](https://github.com/dldevinc/paper-streamfield/tree/v0.18.5) - 2023-12-14

### Features

-   In `ImageCollection` subclasses, you can set the file validators
    with the new `VALIDATORS` attribute.

### Bug Fixes

-   Fixed an issue where it was impossible to delete all variations at once using 
    the `remove_variations` command.

## [0.18.4](https://github.com/dldevinc/paper-streamfield/tree/v0.18.4) - 2023-12-12

### Bug Fixes

-   Removed deprecated `Collection.items` field.
-   Fixed an issue with using deprecated `itemType` property.

## [0.18.1](https://github.com/dldevinc/paper-streamfield/tree/v0.18.1) - 2023-12-12

### Bug Fixes

-   Add missing migration.

## [0.18.0](https://github.com/dldevinc/paper-streamfield/tree/v0.18.0) - 2023-12-12

### ⚠ BREAKING CHANGES

-   Dropped support for Python 3.8.
-   Dropped support for Django versions below 3.2.
-   Added support for Python 3.12.
-   Added support for Django 5.0.
-   Removed deprecated `UnsupportedFileError` exception.
-   Removed deprecated `SizeValidator`.
-   Removed deprecated `FileResource.basename` property.
-   Removed deprecated `FileResource.get_file_url()` method.
-   Removed deprecated `FileResource.attach_file()` method.
-   Removed deprecated `FileResource._attach_file()` method.
-   Removed deprecated `FileResource.rename_file()` method.
-   Removed deprecated `FileResource._rename_file()` method.
-   Removed deprecated `CollectionItemBase.item_type` property.
-   Removed deprecated `CollectionItemBase.get_itemtype_field()` method.
-   Removed deprecated `CollectionFileItemBase.file_supported()` method.
-   Removed deprecated `itemType` key from `CollectionItemBase.as_dict()` output.

### Features

-   In `ImageCollection` subclasses, you can set the file storage path 
    with the new `UPLOAD_TO` attribute.
-   The `--field` parameter in the `recreate_variations` and `remove_variations` 
    management commands is an alias for the `--item-type` parameter.
-   Now, parameters for the `recreate_variations` and `remove_variations` management 
    commands can be positional. Example:
    ```bash
    python3 recreate_variations app.Page background -- desktop mobile
    ```

### Bug Fixes

-   The behavior of `Ctrl+Z` has been fixed when executing management commands.

## [0.17.1](https://github.com/dldevinc/paper-streamfield/tree/v0.17.1) - 2023-11-07

### Features

-   Added the `srcset` field for image resources.
-   Removed the automatic selection of the "[All]" option in the dialogs for 
    the `recreate_variations` and `remove_variations` management commands.

### Bug Fixes

-   Fixed a bug where the number of selected items in a collection was not properly 
    included in the deletion confirmation message.

## [0.17.0](https://github.com/dldevinc/paper-streamfield/tree/v0.17.0) - 2023-10-08

### ⚠ BREAKING CHANGES

-   Added new `mimetype` field.

## [0.16.2](https://github.com/dldevinc/paper-streamfield/tree/v0.16.2) - 2023-09-26

### Features

-   Upscaling is now forced enabled for `2x`, `3x` and `4x` versions.

## [0.16.1](https://github.com/dldevinc/paper-streamfield/tree/v0.16.1) - 2023-09-20

### Bug Fixes

-   Set `default_auto_field` to `django.db.models.BigAutoField`.

## [0.16.0](https://github.com/dldevinc/paper-streamfield/tree/v0.16.0) - 2023-09-10

### ⚠ BREAKING CHANGES

-   Remove Python 3.7 support.

### Features

-   `check_uploads` and `clean_uploads` are now checks existence of the reference 
    from the owner to the resource.

## [0.15.1](https://github.com/dldevinc/paper-streamfield/tree/v0.15.1) - 2023-04-23

### Features

-   Migrate to CSS grids.

## [0.15.0](https://github.com/dldevinc/paper-streamfield/tree/v0.15.0) - 2023-04-16

### ⚠ BREAKING CHANGES

-   Remove Python 3.6 support.
-   Minimum required `paper-admin` version is now `6.0.0`.

## [0.14.1](https://github.com/dldevinc/paper-uploads/tree/v0.14.1) - 2023-02-03

### Features

-   Bind collection widget to `collection--default` CSS-class.

## [0.14.0](https://github.com/dldevinc/paper-uploads/tree/v0.14.0) - 2023-01-09

### Features

-   Add support for `paper-admin` >= 5.0.
-   Increase default value of `min-age` parameter for `clean_uploads`
    and `remove_empty_collections` commands.

## [0.13.0](https://github.com/dldevinc/paper-uploads/tree/v0.13.0) - 2022-10-26

### Features

-   Added `ResourceQuerySet` and inner class `ResourceMeta`.

## [0.12.0](https://github.com/dldevinc/paper-uploads/tree/v0.12.0) - 2022-10-10

### Features

-   Added `ratio` and `hw_ratio` image properties.

## [0.11.5](https://github.com/dldevinc/paper-uploads/tree/v0.11.5) - 2022-10-10

### Features

-   Improved management commands.

## [0.11.4](https://github.com/dldevinc/paper-uploads/tree/v0.11.4) - 2022-08-15

### Features

-   Added default choice for some prompts in management commands.

### Bug Fixes

-   Fixed `remove_variations` management command.

## [0.11.3](https://github.com/dldevinc/paper-uploads/tree/v0.11.3) - 2022-08-15

### Features

-   Updated dependencies.

## [0.11.2](https://github.com/dldevinc/paper-uploads/tree/v0.11.2) - 2022-07-03

### Bug Fixes

-   Fixed `Class constructors cannot be invoked without 'new'` error.

## [0.11.1](https://github.com/dldevinc/paper-uploads/tree/v0.11.1) - 2022-07-03

### Bug Fixes

-   Fixed some typos.

## [0.11.0](https://github.com/dldevinc/paper-uploads/tree/v0.11.0) - 2022-06-02

### ⚠ BREAKING CHANGES

-   Removed `cloudinary` submodule.
-   Removed `file` parameter from `variation_created` signal. Added `name` parameter
    instead.
-   `CollectionModelNotFoundError` and `CollectionItemNotFoundError` exceptions
    have been added.
-   Added `UnsupportedCollectionItemError` exception.

### Features

-   `ContentType.objects.get_for_id()` method has been used to get rid of redundant
    SQL queries.
-   The `get_file_field()` method is now a classmethod.
-   A new `concrete_collection_content_type` field was added to the `Collection`
    and `CollectionItemBase` models.
-   The `Collection.get_items()` now works properly not only with the proxy collection
    models, but also with corresponding concrete model.
-   Field `Collection.items` is now deprecated.

### Bug Fixes

-   Fixed an issue where `remove_empty_collections` command deletes non-empty collections.
-   Fixed an issue where `create_missing_variations` command skips some instaces.

## [0.10.0](https://github.com/dldevinc/paper-uploads/tree/v0.10.0) - 2022-05-23

### ⚠ BREAKING CHANGES

-   The minimum supported version of `paper-admin` is increased from 3.0 to 4.1.0.

## [0.9.3](https://github.com/dldevinc/paper-uploads/tree/v0.9.3) - 2022-05-20

### Features

-   Migrate to `paper-uploader` npm package.

## [0.9.2](https://github.com/dldevinc/paper-uploads/tree/v0.9.2) - 2022-05-19

### Features

-   Export `Uploader` class. It can be accessed via `window.paperUploads.Uploader`.

## [0.9.1](https://github.com/dldevinc/paper-uploads/tree/v0.9.1) - 2022-04-15

### Features

-   Update `npm` dependencies.

## [0.9.0](https://github.com/dldevinc/paper-uploads/tree/v0.9.0) - 2022-03-26

### Features

-   Added `SVGFileField`.

## [0.8.2](https://github.com/dldevinc/paper-uploads/tree/v0.8.2) - 2022-03-25

### Bug Fixes

-   Fixed an issue where file descriptor offset was not reset before `prepare()` call.

## [0.8.1](https://github.com/dldevinc/paper-uploads/tree/v0.8.1) - 2022-02-22

### Bug Fixes

-   Fixed an issue with serialization.

## [0.8.0](https://github.com/dldevinc/paper-uploads/tree/v0.8.0) - 2022-02-21

### ⚠ BREAKING CHANGES

-   Changed default values `FILES_UPLOAD_TO`, `IMAGES_UPLOAD_TO`,
    `COLLECTION_FILES_UPLOAD_TO` and `COLLECTION_IMAGES_UPLOAD_TO` settings.

### Features

-   Added field checks for `upload_to` parameter.
-   Added new `FileFieldResource.generate_filename()` method.

## [0.8.0rc4](https://github.com/dldevinc/paper-uploads/tree/v0.8.0rc4) - 2022-02-21

### Features

-   Added new method `Collection.get_last_modified()`.
-   Add an ability to specify `storage` and `upload_to` for particular fields.
-   The `basename` field has been renamed to `resource_name`.
-   Management commands rewritten.
-   Added `create_missing_variations` management command.
-   Method `get_file_url()` is now deprecated.

### Bug Fixes

-   Fix a not creation variations with non-filesystem storages.

## [0.8.0rc3](https://github.com/dldevinc/paper-uploads/tree/v0.8.0rc3) - 2022-02-02

### ⚠ BREAKING CHANGES

-   Method `set_owner_from()` has been rewritten and renamed to `set_owner_field()`.
-   **Note**: `paper_uploads.cloudinary` will be moved to a separate package.

### Features

-   `SizeValidator` is now deprecated in favor of `MaxSizeValidator`.
-   Allow `str` and `Path` as the parameter of `attach()` method.
-   Allow overriding variation name with option `name`.

### Bug Fixes

-   Fixed `remove_variations` and `recreate_variations` management commands.

## [0.8.0rc2](https://github.com/dldevinc/paper-uploads/tree/v0.8.0rc2) - 2022-02-01

### Features

-   Add Django 4.0 support
-   Add Python 3.10 support

### Bug Fixes

-   Fixed infinite recursion when a collection model was removed, but the corresponding
    `ContentType` remains.

## [0.8.0rc1](https://github.com/dldevinc/paper-uploads/tree/v0.8.0rc1) - 2021-11-22

### ⚠ BREAKING CHANGES

-   Mixin `BacklinkModelMixin` has been moved from `Resource` class to
    `UploadedFile`, `UploadedImage` and `CollectionBase`.
    This update will remove `owner_XXX` fields from collection items.
    Run `makemigrations` and `migrate` commands to apply the change to your data.
-   Field `CollectionItem.item_type` is now deprecated in favor of `type`.
-   Management commands rewritten.
-   Removed `COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS` setting.

#### Internal changes

-   Added `change_form_class` property to `UploadedFile` and `UploadedImage`.
    This field can be used to specify a custom dialog form for a given model.
-   Disabled implicit `content_type` filtration for concrete collection models.
-   Added composite index for collection items on `collection_id` and `collection_content_type` fields.
-   `FileResource`'s method `get_basename()` has been renamed to `get_caption()`.
-   `FileWidgetBase` has been renamed to `FileResourceWidgetBase`.
-   `FileUploaderWidgetMixin` has been renamed to `DisplayFileLimitationsMixin`.
-   `admin.base.UploadedFileBase` has been renamed to `ResourceAdminBase`.
-   `UploadedFileBaseForm` has been renamed to `ChangeFileResourceDialogBase`.
-   `UploadedFileDialog` has been renamed to `ChangeUploadedFileDialog`.
-   `UploadedImageDialog` has been renamed to `ChangeUploadedImageDialog`.
-   `FileItemDialog` has been renamed to `ChangeFileItemDialog`.
-   `ImageItemDialog` has been renamed to `ChangeImageItemDialog`.
-   Changed some admin URLs for collections.
-   Added new `InvalidItemType` exception.
-   Deleted `FileNotFoundError` exception.

### Features

-   Implement `__iter__()` for `CollectionBase`.
-   Method `.attach_file()` is now deprecated in favor of `.attach()`.
-   Method `.rename_file()` is now deprecated in favor of `.rename()`.
-   Method `.file_supported()` is now deprecated in favor of `.accept()`.
-   Exception `UnsupportedFileError` is now deprecated in favor of `UnsupportedResource`.
-   Added an ability to override the `admin_preview` variation for `ImageItem`
    via `VARIATIONS` property.
-   Updated view classes for easier customization.
-   `rename_file()` will use `recut_async()` when supported.

### Bug Fixes

-   Fixed caption update for collection items.

## [0.7.0](https://github.com/dldevinc/paper-uploads/tree/v0.7.0) - 2021-11-09

### Features

-   Add an ability to override parent link field for collection item models inherited
    from an abstract class (e.g., `FileItemBase`, `ImageItemBase`).
-   Added new method `set_owner_from()`.
-   Added new method `Collection.get_item_model()`.

## [0.6.3](https://github.com/dldevinc/paper-uploads/tree/v0.6.3) - 2021-11-06

### Features

-   Add abstract base classes for collection items.

### Bug Fixes

-   Fixed image recut with `python-rq`.
-   Fixed `RecursionError` when deleting a collection.

## [0.6.2](https://github.com/dldevinc/paper-uploads/tree/v0.6.2) - 2021-11-02

### Features

-   New `remove_empty_collections` management command.

### Bug Fixes

-   Support explicit cascading deletion with `FileField` and `ImageField`.

## [0.6.1](https://github.com/dldevinc/paper-uploads/tree/v0.6.1) - 2021-10-20

### Features

-   Add an ability to override admin model's views.

## [0.6.0](https://github.com/dldevinc/paper-uploads/tree/v0.6.0) - 2021-09-10

### ⚠ BREAKING CHANGES

-   Removed `CloudinaryCollection` class.

### Features

-   Add a method `get_file_folder` returning storage directory.
    Override this method to customize the upload folder.

### Bug Fixes

-   Fix `RecursionError` when deleting ImageCollection.

## [0.5.2](https://github.com/dldevinc/paper-uploads/tree/v0.5.2) - 2021-09-03

### Bug Fixes

-   Scale `max_width` and `max_height` for Retina versions.

## [0.5.1](https://github.com/dldevinc/paper-uploads/tree/v0.5.1) - 2021-08-25

### Features

-   Make it possible to rename files with the same name.
-   Add an ability to override `type` and `resource_type` options for Cloudinary fields.
-   Switch from Travis CI to GitHub Actions.
-   Update npm dependencies.

## [0.5.0](https://github.com/dldevinc/paper-uploads/tree/v0.5.0) - 2021-07-10

### ⚠ BREAKING CHANGES

-   Drop support for Django versions before 2.2.
-   Requires `paper-admin` >= 3.0.
-   Migrate from `fine-uploader` to `dropzone.js`.
-   Removed default permissions from all Django models.
-   Collection previews has been reduced from `192x148` to `180x135`.

### Features

-   Added Python 3.9 support.
-   Added `remove_variations` management command.
-   The `recreate_variations` management command has been completely rewritten.

## [0.4.5](https://github.com/dldevinc/paper-uploads/tree/v0.4.5) - 2020-10-26

-   Add `cloudinary/helpers.py` file

## [0.4.4](https://github.com/dldevinc/paper-uploads/tree/v0.4.4) - 2020-10-19

-   Fix missing templates

## [0.4.3](https://github.com/dldevinc/paper-uploads/tree/v0.4.3) - 2020-10-19

-   Fix model checks

## [0.4.2](https://github.com/dldevinc/paper-uploads/tree/v0.4.2) - 2020-10-19

-   Fix missing static files

## [0.4.0](https://github.com/dldevinc/paper-uploads/tree/v0.4.0) - 2020-09-04

-   **Rewritten from scratch**
-   Added `CLOUDINARY_TYPE` setting
-   Added `CLOUDINARY_TEMP_DIR` setting
-   Rename `CLOUDINARY` setting to `CLOUDINARY_UPLOADER_OPTIONS`
-   Rename `ItemField` to `CollectionItem`
-   Rename `MimetypeValidator` to `MimeTypeValidator`
-   Signal `variation_created` was added
-   Migrate to DropBox's checksum realization
-   Remove postprocessing
-   Upgrade development environment
