import os

import pytest
from django.utils.timezone import now

from paper_uploads.models import UploadedImage

from ..dummy import *


@pytest.fixture(scope='class')
def uploaded_image(class_scoped_db):
    resource = UploadedImage(
        owner_app_label='app',
        owner_model_name='imageexample',
        owner_fieldname='image',
    )
    with open(NATURE_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield resource

    resource.delete_file()
    resource.delete()


@pytest.mark.django_db
class TestUploadedImage:
    def test_name(self, uploaded_image):
        assert uploaded_image.name == 'Nature Tree'

    def test_extension(self, uploaded_image):
        assert uploaded_image.extension == 'jpeg'

    def test_size(self, uploaded_image):
        assert uploaded_image.size == 672759

    def test_content_hash(self, uploaded_image):
        assert uploaded_image.content_hash == 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'

    def test_file_exists(self, uploaded_image):
        assert uploaded_image.file_exists() is True

    def test_get_basename(self, uploaded_image):
        assert uploaded_image.get_basename() == 'Nature Tree.jpeg'

    def test_get_file_name(self, uploaded_image):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_image.get_file_name() == 'images/{}/Nature_Tree.Jpeg'.format(date)

    def test_get_file_url(self, uploaded_image):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_image.get_file_url() == '/media/images/{}/Nature_Tree.Jpeg'.format(date)

    def test_width(self, uploaded_image):
        assert uploaded_image.width == 1534

    def test_height(self, uploaded_image):
        assert uploaded_image.height == 2301

    def test_as_dict(self, uploaded_image):
        date = now().date().strftime('%Y-%m-%d')
        assert uploaded_image.as_dict() == {
            'id': 1,
            'name': 'Nature Tree',
            'extension': 'jpeg',
            'size': 672759,
            'url': '/media/images/{}/Nature_Tree.Jpeg'.format(date),
            'file_info': '(jpeg, 1534x2301, 657.0\xa0KB)',
            'width': 1534,
            'height': 2301,
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
