import pytest
from paper_uploads.models.collection import ImageItem


@pytest.mark.django_db
def test_only():
    qs = ImageItem.objects.only("pk")
    fields, defer = qs.query.deferred_loading
    assert set(fields) == {
        "collectionitembase_ptr", "collection_content_type_id", "polymorphic_ctype_id",
        "type"
    }


@pytest.mark.django_db
def test_defer():
    qs = ImageItem.objects.defer("type", "order")
    fields, defer = qs.query.deferred_loading
    assert set(fields) == {"order", }
