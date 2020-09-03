import posixpath

import cloudinary.exceptions
import pytest
from cloudinary import uploader

from app.models import CloudinaryImageExample
from paper_uploads.cloudinary.models import CloudinaryImage

from ... import utils
from ...dummy import *
from ...models.test_base import (
    TestEmptyFileFieldResource,
    TestImageDelete,
    TestImageRename,
)
from .test_base import CloudinaryFileResource


class TestCloudinaryImage(CloudinaryFileResource):
    resource_url = '/media/images/%Y-%m-%d'
    resource_location = 'images/%Y-%m-%d'
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = 'app'
    owner_model_name = 'cloudinaryimageexample'
    owner_fieldname = 'image'
    owner_class = CloudinaryImageExample
    file_field_name = 'file'

    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryImage(
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

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == 'private'
        assert file_field.resource_type == 'image'

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}')
        assert public_id == utils.get_target_filepath(pattern, public_id)

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}')
        assert file_name == utils.get_target_filepath(pattern, file_name)

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
            'file_info': '(jpg, 1534x2301, 657.0\xa0KB)',
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }


class TestCloudinaryImageRename(TestImageRename):
    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryImage(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_image_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name

        storage.resource.rename_file('new_image_name.png')

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_exists(self, storage):
        file = storage.resource.get_file()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_source_name,
                type=file.type,
                resource_type=file.resource_type
            )

    def test_new_file_exists(self, storage):
        file = storage.resource.get_file()
        uploader.explicit(
            file.name,
            type=file.type,
            resource_type=file.resource_type
        )

    def test_old_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            'images/%Y-%m-%d/old_image_name{suffix}',
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            'images/%Y-%m-%d/new_image_name{suffix}',
            file.name
        )


class TestCloudinaryImageDelete(TestImageDelete):
    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryImage(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name

        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            'images/%Y-%m-%d/old_name{suffix}',
            storage.old_source_name
        )

    def test_file_not_exists(self, storage):
        file_field = storage.resource.get_file_field()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_source_name,
                type=file_field.type,
                resource_type=file_field.resource_type
            )


class TestEmptyCloudinaryFile(TestEmptyFileFieldResource):
    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryImage()
        yield

    def test_path(self, storage):
        pass
