import os

import pytest
from django.conf import settings
from django.utils.timezone import now

from paper_uploads.models import UploadedImage

NASA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/milky-way-nasa.jpg')
CALLIPHORA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/calliphora.jpg')
NATURE_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/nature.jpeg')


@pytest.fixture(scope='class')
def uploaded_image(class_scoped_db):
    resource = UploadedImage(
        owner_app_label='app',
        owner_model_name='imageexample',
        owner_fieldname='image',
    )
    with open(CALLIPHORA_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield resource

    resource.delete_file()
    resource.delete()


@pytest.mark.django_db
class TestUploadedImage:
    def test_name(self, uploaded_image):
        assert uploaded_image.name == 'calliphora'

    def test_extension(self, uploaded_image):
        assert uploaded_image.extension == 'jpg'

    def test_size(self, uploaded_image):
        assert uploaded_image.size == 254766

    def test_content_hash(self, uploaded_image):
        assert uploaded_image.content_hash == 'd4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386'

    def test_file_exists(self, uploaded_image):
        assert uploaded_image.file_exists() is True

    def test_get_basename(self, uploaded_image):
        assert uploaded_image.get_basename() == 'calliphora.jpg'

    def test_get_file_name(self, uploaded_image):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_image.get_file_name() == 'images/{}/calliphora.jpg'.format(date)

    def test_get_file_url(self, uploaded_image):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_image.get_file_url() == '/media/images/{}/calliphora.jpg'.format(date)

    def test_as_dict(self, uploaded_image):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_image.as_dict() == {
            'id': 1,
            'name': 'calliphora',
            'extension': 'jpg',
            'size': 254766,
            'url': '/media/images/{}/calliphora.jpg'.format(date),
            'file_info': '(jpg, 804x1198, 248.8\xa0KB)',
            'width': 804,
            'height': 1198,
            'cropregion': '',
            'title': '',
            'description': ''
        }


@pytest.mark.django_db
class TestUploadedImageExists:
    def test_files(self, uploaded_image):
        source_path = uploaded_image.path
        desktop_path = uploaded_image.desktop.path
        mobile_path = uploaded_image.mobile.path

        assert os.path.exists(source_path) is True
        assert os.path.exists(desktop_path) is True
        assert os.path.exists(mobile_path) is True

        uploaded_image.delete_file()

        assert os.path.exists(source_path) is False
        assert os.path.exists(desktop_path) is False
        assert os.path.exists(mobile_path) is False
