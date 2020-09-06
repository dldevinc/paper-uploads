from django.db.models.signals import Signal

# изменение контрольной суммы файла
checksum_update = Signal(providing_args=["instance", "checksum"])

# создание / перезапись (recut) файла вариации изображения
variation_created = Signal(providing_args=["instance", "file"])

# присоединение файла к ресурсу
pre_attach_file = Signal(providing_args=["instance", "file", "options"])
post_attach_file = Signal(providing_args=["instance", "file", "options", "response"])

# переименование файла
pre_rename_file = Signal(providing_args=["instance", "old_name", "new_name", "options"])
post_rename_file = Signal(providing_args=["instance", "old_name", "new_name", "options", "response"])

# удаление файла
pre_delete_file = Signal(providing_args=["instance", "options"])
post_delete_file = Signal(providing_args=["instance", "options", "response"])

# изменен порядок элементов коллекции
collection_reordered = Signal(providing_args=["instance"])
