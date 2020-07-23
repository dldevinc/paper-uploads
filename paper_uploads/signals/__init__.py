from django.db.models.signals import Signal

# Хэш файла изменился. Это происходит либо в случае создания нового файла,
# либо при изменении контента уже существующего файла.
content_hash_update = Signal(providing_args=["instance", "content_hash"])

# создание / перезапись (recut) файла вариации изображения
variation_created = Signal(providing_args=["instance", "file"])

# присоединение файла к ресурсу
pre_attach_file = Signal(providing_args=["instance", "file", "options"])
post_attach_file = Signal(providing_args=["instance", "file", "options", "response"])

# переименование файла
pre_rename_file = Signal(providing_args=["instance", "new_name"])
post_rename_file = Signal(providing_args=["instance", "new_name"])

# удаление файла
pre_delete_file = Signal(providing_args=["instance"])
post_delete_file = Signal(providing_args=["instance"])

# изменен порядок элементов коллекции
collection_reordered = Signal(providing_args=["instance"])
