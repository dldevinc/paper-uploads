import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import File
from PIL import Image
from tests.app.models import Page

from .. import utils, validators


def test_remove_dulpicates():
    assert utils.remove_dulpicates(
        ['apple', 'banana', 'apple', 'apple', 'banana', 'orange', 'banana']
    ) == ('apple', 'banana', 'orange')


def test_run_validators():
    with File(io.BytesIO(), name='file.jpeg') as file:
        with Image.new('RGB', (640, 480)) as img:
            img.save(file, format='JPEG')

        try:
            utils.run_validators(
                file,
                [
                    validators.ExtensionValidator(['jpg']),
                    validators.ImageMinSizeValidator(800, 600),
                    validators.ImageMaxSizeValidator(1024, 800),
                ],
            )
        except ValidationError as exc:
            assert len(exc.messages) == 2
            assert (
                "has an invalid extension. Valid extension(s): jpg" in exc.messages[0]
            )
            assert (
                "is too small. Image should be at least 800x600 pixels."
                in exc.messages[1]
            )


def test_lowercase_copy():
    assert utils.lowercase_copy({'Fruit': 'banana', 'color': 'Red',}) == {
        'fruit': 'banana',
        'color': 'Red',
    }


@pytest.mark.django_db
def test_get_instance():
    page = Page.objects.create(id=1, header='Testing',)

    assert utils.get_instance('app', 'page', 1) == page
    assert utils.get_instance('app', 'page', 1, using='default') == page

    with pytest.raises(Page.DoesNotExist):
        assert utils.get_instance('app', 'page', 2)
