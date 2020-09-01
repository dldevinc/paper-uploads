import cloudinary
import pytest
from cloudinary import uploader

from app.models import CloudinaryFileExample
from paper_uploads.cloudinary.models import CloudinaryFile
from paper_uploads.conf import settings

from ... import utils
from ...dummy import *
from ...models.test_base import (
    TestEmptyFileFieldResource,
    TestFileDelete,
    TestFileFieldResource,
    TestFileRename,
)


class TestCloudinaryFile(TestFileFieldResource):
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 672759
    resource_hash = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    file_field_name = 'file'

    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryFile(
            owner_app_label='app',
            owner_model_name='cloudinaryfileexample',
            owner_fieldname='file'
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
        assert file_field.resource_type == 'raw'

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_get_owner_model(self, storage):
        assert storage.resource.get_owner_model() is CloudinaryFileExample

    def test_get_owner_field(self, storage):
        assert storage.resource.get_owner_field() is CloudinaryFileExample._meta.get_field('file')

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'files/%Y-%m-%d/Nature_Tree{suffix}.Jpeg',
            file_name
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url.startswith('https://res.cloudinary.com/')

    def test_path(self, storage):
        # Cloudinary has no path
        pass

    def test_url(self, storage):
        assert storage.resource.url.startswith('https://res.cloudinary.com/')

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'file_info': '(Jpeg, 657.0\xa0KB)',
            'url': storage.resource.get_file_url(),
        }

    def test_get_cloudinary_options(self, storage):
        options = storage.resource.get_cloudinary_options()
        folder = utils.get_target_filepath(settings.FILES_UPLOAD_TO, '')
        assert options == {
            'use_filename': True,
            'unique_filename': True,
            'overwrite': True,
            'folder': folder
        }


class TestCloudinaryFileRename(TestFileRename):
    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryFile(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name

        storage.resource.rename_file('new_name.png')

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_exists(self, storage):
        file = storage.resource.get_file()
        uploader.explicit(
            file.name,
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
            'files/%Y-%m-%d/old_name{suffix}.jpg',
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            'files/%Y-%m-%d/new_name{suffix}.png',
            file.name
        )


class TestCloudinaryFileDelete(TestFileDelete):
    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryFile(
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
            'files/%Y-%m-%d/old_name{suffix}.jpg',
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
        storage.resource = CloudinaryFile()
        yield

    def test_path(self, storage):
        pass
