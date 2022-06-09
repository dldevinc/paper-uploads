from threading import local

import pytest
from django.core.management import call_command
from django.utils.timezone import now


@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    pass


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "tests/test_fixtures.json")


@pytest.fixture(scope="class")
def storage(request, django_db_setup, django_db_blocker):
    """
    Инициализация тестируемых объектов для класса.
    В отличие от fixture, позволяет использовать
    наследование классов, наследуя тем самым методы,
    и, в то же время, переопределять тестируемый
    объект.

        class TestShape:
            @classmethod
            def init_class(cls, storage):
                storage.object = Shape(...)
                yield
                storage.object.delete()

            def test_smthg(self, storage):
                assert storage.object.pk == 1

        class TestSquare(TestShape):
            @classmethod
            def init_class(cls, storage):
                storage.object = Square(...)
                yield
                storage.object.delete()
    """
    with django_db_blocker.unblock():
        storage = local()
        if hasattr(request.cls, "init_class"):
            gen = request.cls.init_class(storage)
            next(gen)

        # Time right after `init()` call. For date / time tests.
        storage.now = now()

        yield storage

        # release resources
        try:
            next(gen)
        except StopIteration:
            pass
