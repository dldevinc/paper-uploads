import os

import pytest
from django.conf import settings
from django.utils.timezone import now

from paper_uploads.models import UploadedFile

NASA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/milky-way-nasa.jpg')
CALLIPHORA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/calliphora.jpg')
NATURE_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/nature.jpeg')


@pytest.fixture(scope='class')
def uploaded_file(class_scoped_db):
    resource = UploadedFile(
        owner_app_label='app',
        owner_model_name='fileexample',
        owner_fieldname='file',
    )
    with open(CALLIPHORA_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield resource

    resource.delete_file()
    resource.delete()


@pytest.mark.django_db
class TestUploadedFile:
    def test_name(self, uploaded_file):
        assert uploaded_file.name == 'calliphora'

    def test_display_name(self, uploaded_file):
        assert uploaded_file.display_name == 'calliphora'

    def test_extension(self, uploaded_file):
        assert uploaded_file.extension == 'jpg'

    def test_size(self, uploaded_file):
        assert uploaded_file.size == 254766

    def test_content_hash(self, uploaded_file):
        assert uploaded_file.content_hash == 'd4dec03fae591f0c89776c57f8b5d721c930f5f7cb1b32d456f008700a432386'

    def test_file_exists(self, uploaded_file):
        assert uploaded_file.file_exists() is True

    def test_get_basename(self, uploaded_file):
        assert uploaded_file.get_basename() == 'calliphora.jpg'

    def test_get_file_name(self, uploaded_file):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_file.get_file_name() == 'files/{}/calliphora.jpg'.format(date)

    def test_get_file_url(self, uploaded_file):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_file.get_file_url() == '/media/files/{}/calliphora.jpg'.format(date)

    def test_as_dict(self, uploaded_file):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_file.as_dict() == {
            'id': 1,
            'name': 'calliphora',
            'extension': 'jpg',
            'size': 254766,
            'url': '/media/files/{}/calliphora.jpg'.format(date),
            'file_info': '(jpg, 248.8\xa0KB)'
        }


@pytest.mark.django_db
class TestUploadedFileExists:
    def test_files(self, uploaded_file):
        source_path = uploaded_file.path
        assert os.path.exists(source_path) is True
        uploaded_file.delete_file()
        assert os.path.exists(source_path) is False
