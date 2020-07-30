# Change Log

## [0.3.0](https://github.com/dldevinc/paper-uploads/tree/v0.3.0) - 2020-07-22
- Rename `ReverseFieldModelMixin` to `BacklinkModelMixin`
- Rename `ItemField` to `CollectionItem`
- Rename `HashableResourceMixin` to `HashableResource`
- Rename `hash_updated` signal to `content_hash_update`
- Signal `variation_created` was added
- Use DropBox checksum realization.
- Remove postprocessing
- `utils.run_validators()` and `utils.get_instance()` was moved to `helpers.py`
- `utils.lowercase_copy()` renamed to `utils.lowercased_dict_keys()`
- Drop `paper-admin` dependency
- Upgrade development environment
