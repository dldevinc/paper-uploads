from django.db.models.signals import Signal

collection_reordered = Signal(providing_args=["instance"])
hash_updated = Signal(providing_args=["instance", "hash"])

pre_attach_file = Signal(providing_args=["instance", "file", "options"])
post_attach_file = Signal(providing_args=["instance", "file", "response"])

pre_rename_file = Signal(providing_args=["instance", "new_name"])
post_rename_file = Signal(providing_args=["instance", "new_name"])

pre_delete_file = Signal(providing_args=["instance"])
post_delete_file = Signal(providing_args=["instance"])
