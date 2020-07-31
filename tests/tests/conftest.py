from threading import local

import pytest
import pytest_django.fixtures


@pytest.fixture(scope="class")
def class_scoped_db(request, django_db_setup, django_db_blocker):
    """
    Like `db` fixture, but class-scoped.
    """
    if "django_db_reset_sequences" in request.fixturenames:
        request.getfixturevalue("django_db_reset_sequences")
    if (
        "transactional_db" in request.fixturenames
        or "live_server" in request.fixturenames
    ):
        request.getfixturevalue("transactional_db")
    else:
        pytest_django.fixtures._django_db_fixture_helper(request, django_db_blocker, transactional=False)


@pytest.fixture(scope='class')
def storage(request, class_scoped_db):
    """
    Инициализация тестируемых объектов для класса.
    В отличие от fixture, позволяет использовать
    наследование классов, наследуя тем самым методы,
    и, в то же время, переопределять тестируемый
    объект.

        class TestShape:
            @staticmethod
            def init(storage):
                storage.object = Shape(...)
                yield
                storage.object.delete()

            def test_smthg(self, storage):
                assert storage.object.pk == 1

        class TestSquare(TestShape):
            @staticmethod
            def init(storage):
                storage.object = Square(...)
                yield
                storage.object.delete()
    """
    storage = local()
    gen = request.cls.init(storage)

    next(gen)
    yield storage

    try:
        next(gen)
    except StopIteration:
        pass
