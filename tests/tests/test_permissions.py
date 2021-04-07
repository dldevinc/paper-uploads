from django.apps import apps
from django.contrib.auth.management import _get_builtin_permissions


def test_permissions():
    for app_name in {"paper_uploads", "paper_uploads_cloudinary"}:
        app_config = apps.get_app_config(app_name)
        for klass in app_config.get_models():
            assert not _get_builtin_permissions(klass._meta)
