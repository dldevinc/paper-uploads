from typing import Iterable
from django.db import DEFAULT_DB_ALIAS
from .utils import get_instance


def recut_collection(app_label: str, model_name: str, object_id: int,
        names: Iterable[str] = None, using: str = DEFAULT_DB_ALIAS):
    collection = get_instance(app_label, model_name, object_id, using=using)
    collection._recut_sync(names, using=using)
