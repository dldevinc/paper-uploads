import os

import pytest
from django.utils.timezone import now

from paper_uploads.models import UploadedFile

from ..dummy import *


@pytest.fixture(scope='class')
def uploaded_file(class_scoped_db):
    resource = UploadedFile(
        owner_app_label='app',
        owner_model_name='fileexample',
        owner_fieldname='file',
    )
    with open(DOCUMENT_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield resource

    resource.delete_file()
    resource.delete()


@pytest.mark.django_db
class TestUploadedFile:
    def test_name(self, uploaded_file):
        assert uploaded_file.name == 'document'

    def test_display_name(self, uploaded_file):
        assert uploaded_file.display_name == 'document'

    def test_extension(self, uploaded_file):
        assert uploaded_file.extension == 'pdf'

    def test_size(self, uploaded_file):
        assert uploaded_file.size == 3028

    def test_content_hash(self, uploaded_file):
        assert uploaded_file.content_hash == '93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e'

    def test_file_exists(self, uploaded_file):
        assert uploaded_file.file_exists() is True

    def test_get_basename(self, uploaded_file):
        assert uploaded_file.get_basename() == 'document.pdf'

    def test_get_file_name(self, uploaded_file):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_file.get_file_name() == 'files/{}/document.pdf'.format(date)

    def test_get_file_url(self, uploaded_file):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_file.get_file_url() == '/media/files/{}/document.pdf'.format(date)

    def test_as_dict(self, uploaded_file):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_file.as_dict() == {
            'id': 1,
            'name': 'document',
            'extension': 'pdf',
            'size': 3028,
            'url': '/media/files/{}/document.pdf'.format(date),
            'file_info': '(pdf, 3.0\xa0KB)'
        }


@pytest.mark.django_db
class TestUploadedFileExists:
    def test_files(self, uploaded_file):
        source_path = uploaded_file.path
        assert os.path.exists(source_path) is True
        uploaded_file.delete_file()
        assert os.path.exists(source_path) is False
