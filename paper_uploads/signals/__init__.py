from django.db.models.signals import Signal

# изменение контрольной суммы файла
checksum_update = Signal()

# создание / перезапись (recut) файла вариации изображения
variation_created = Signal()

# присоединение файла к ресурсу
pre_attach_file = Signal()
post_attach_file = Signal()

# переименование файла
pre_rename_file = Signal()
post_rename_file = Signal()

# удаление файла
pre_delete_file = Signal()
post_delete_file = Signal()

# изменен порядок элементов коллекции
collection_reordered = Signal()
