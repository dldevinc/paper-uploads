from django.db.models.signals import Signal

collection_reordered = Signal(providing_args=["instance"])
