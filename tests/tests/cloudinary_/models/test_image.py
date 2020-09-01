from cloudinary import uploader

from app.models import CloudinaryImageExample
from paper_uploads.cloudinary.models import CloudinaryImage
from paper_uploads.conf import settings

from ... import utils
from ...dummy import *
from ...models.test_base import TestImageFieldResource, TestEmptyFileFieldResource


class TestCloudinaryImage(TestImageFieldResource):
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'  # Cloudinary extension format
    resource_size = 672759
    resource_hash = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    file_field_name = 'file'

    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryImage(
            title='Calliphora',
            description='Calliphora is a genus of blow flies, also known as bottle flies',
            owner_app_label='app',
            owner_model_name='cloudinaryimageexample',
            owner_fieldname='image'
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

    def test_get_owner_model(self, storage):
        assert storage.resource.get_owner_model() is CloudinaryImageExample

    def test_get_owner_field(self, storage):
        assert storage.resource.get_owner_field() is CloudinaryImageExample._meta.get_field('image')

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'images/%Y-%m-%d/Nature_Tree{suffix}',
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
            'width': 1534,
            'height': 2301,
            'cropregion': '',
            'title': 'Calliphora',
            'description': 'Calliphora is a genus of blow flies, also known as bottle flies',
            'file_info': '(jpg, 1534x2301, 657.0\xa0KB)',
            'url': storage.resource.get_file_url(),
        }

    def test_get_cloudinary_options(self, storage):
        options = storage.resource.get_cloudinary_options()
        folder = utils.get_target_filepath(settings.IMAGES_UPLOAD_TO, '')
        assert options == {
            'use_filename': True,
            'unique_filename': True,
            'overwrite': True,
            'folder': folder
        }


class TestRenameFile:
    def test_rename_file(self):
        resource = CloudinaryImage(
            owner_app_label='app',
            owner_model_name='fileexample',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert resource.file_exists() is True

        resource.rename_file('files/new_name.PNG')

        uploader.explicit(
            resource.get_file_name(),
            type=resource.get_file().type,
            resource_type=resource.get_file().resource_type,
        )
        assert resource.file_exists() is True

        file_name = resource.get_file_name()
        assert file_name == 'files/new_name.PNG'

        resource.delete_file()


class TestEmptyCloudinaryFile(TestEmptyFileFieldResource):
    @classmethod
    def init(cls, storage):
        storage.resource = CloudinaryImage()
        yield

    def test_path(self, storage):
        pass
