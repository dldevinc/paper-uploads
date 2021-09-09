import os

from app.models import ImageExample
from paper_uploads.models import UploadedImage

from ..dummy import *
from .test_base import (
    TestImageAttach,
    TestImageDelete,
    TestImageEmpty,
    TestImageRename,
    TestVersatileImageResource,
)


class TestUploadedImage(TestVersatileImageResource):
    resource_url = '/media/images/%Y-%m-%d'
    resource_location = 'images/%Y-%m-%d'
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = 'app'
    owner_model_name = 'imageexample'
    owner_fieldname = 'image'
    owner_class = ImageExample
    file_field_name = 'file'

    @classmethod
    def init_class(cls, storage):
        storage.resource = UploadedImage(
            title='Calliphora',
            description='Calliphora is a genus of blow flies, also known as bottle flies',
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'width': 1534,
            'height': 2301,
            'cropregion': '',
            'title': 'Calliphora',
            'description': 'Calliphora is a genus of blow flies, also known as bottle flies',
            'file_info': '(jpg, 1534x2301, 672.8\xa0KB)',
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }


class TestUploadedImageAttach(TestImageAttach):
    resource_class = UploadedImage


class TestUploadedImageRename(TestImageRename):
    resource_class = UploadedImage
    resource_location = 'images/%Y-%m-%d'
    owner_app_label = 'app'
    owner_model_name = 'imageexample'
    owner_fieldname = 'image'

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            owner_app_label='app',
            owner_model_name='imageexample',
            owner_fieldname='image'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_desktop_name = storage.resource.desktop.name
        storage.old_mobile_name = storage.resource.mobile.name

        storage.old_source_path = file.path
        storage.old_desktop_path = storage.resource.desktop.path
        storage.old_mobile_path = storage.resource.mobile.path

        storage.resource.rename_file('new_name.png')

        yield

        os.remove(storage.old_source_path)
        os.remove(storage.old_desktop_path)
        os.remove(storage.old_mobile_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestUploadedImageDelete(TestImageDelete):
    resource_class = UploadedImage
    resource_location = 'images/%Y-%m-%d'
    owner_app_label = 'app'
    owner_model_name = 'imageexample'
    owner_fieldname = 'image'

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_desktop_name = storage.resource.desktop.name
        storage.old_mobile_name = storage.resource.mobile.name

        storage.old_source_path = file.path
        storage.old_desktop_path = storage.resource.desktop.path
        storage.old_mobile_path = storage.resource.mobile.path

        storage.resource.delete_file()

        yield

        storage.resource.delete()


class TestUploadedImageEmpty(TestImageEmpty):
    recource_class = UploadedImage


class TestUploadedImageExists:
    @staticmethod
    def init_class(storage):
        storage.resource = UploadedImage(
            owner_app_label='app',
            owner_model_name='imageexample',
            owner_fieldname='image'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        try:
            storage.resource.delete_file()
        except ValueError:
            pass

        storage.resource.delete()

    def test_files(self, storage):
        source_path = storage.resource.path
        desktop_path = storage.resource.desktop.path
        mobile_path = storage.resource.mobile.path

        assert os.path.exists(source_path) is True
        assert os.path.exists(desktop_path) is True
        assert os.path.exists(mobile_path) is True

        storage.resource.delete_file()

        assert os.path.exists(source_path) is False
        assert os.path.exists(desktop_path) is False
        assert os.path.exists(mobile_path) is False
