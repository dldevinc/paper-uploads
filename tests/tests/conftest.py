import pytest
import pytest_django.fixtures


@pytest.fixture(scope="class")
def class_scoped_db(request, django_db_setup, django_db_blocker):
    if "django_db_reset_sequences" in request.fixturenames:
        request.getfixturevalue("django_db_reset_sequences")
    if (
        "transactional_db" in request.fixturenames
        or "live_server" in request.fixturenames
    ):
        request.getfixturevalue("transactional_db")
    else:
        pytest_django.fixtures._django_db_fixture_helper(request, django_db_blocker, transactional=False)
