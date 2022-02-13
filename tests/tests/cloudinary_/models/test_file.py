import posixpath
from contextlib import contextmanager

import cloudinary.exceptions
import pytest
from cloudinary import uploader
from django.utils.crypto import get_random_string

from app.models import CloudinaryFileExample
from paper_uploads.cloudinary.models import CloudinaryFile

from ... import utils
from ...dummy import *
from ...mixins import BacklinkModelTestMixin
from ...models.test_dummy import (
    TestFileFieldResourceAttach,
    TestFileFieldResourceDelete,
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
)
from .test_base import CloudinaryFileResource


class TestCloudinaryFile(BacklinkModelTestMixin, CloudinaryFileResource):
    resource_url = '/media/files/%Y-%m-%d'
    resource_location = 'files/%Y-%m-%d'
    resource_basename = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_fieldname = 'file'
    owner_model = CloudinaryFileExample
    file_field_name = 'file'

    @classmethod
    def init_class(cls, storage):
        storage.resource = CloudinaryFile()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(NATURE_FILEPATH)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_basename

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == 'private'
        assert file_field.resource_type == 'raw'

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}.Jpeg')
        assert public_id == utils.get_target_filepath(pattern, public_id)

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}.Jpeg')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_basename,
            'extension': self.resource_extension,
            'caption': '{}.{}'.format(
                self.resource_basename,
                self.resource_extension
            ),
            'size': self.resource_size,
            'file_info': '(Jpeg, 672.8\xa0KB)',
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }


class TestCloudinaryFileAttach(TestFileFieldResourceAttach):
    resource_class = CloudinaryFile

    @contextmanager
    def get_resource(self):
        resource = self.resource_class()
        try:
            yield resource
        finally:
            resource.delete_file()


class TestCloudinaryFileRename(BacklinkModelTestMixin, TestFileFieldResourceRename):
    resource_class = CloudinaryFile
    resource_location = 'files/%Y-%m-%d'
    owner_fieldname = 'file'
    owner_model = CloudinaryFileExample

    @classmethod
    def init_class(cls, storage):
        storage.uid = get_random_string(5)
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(NATURE_FILEPATH, name='old_file_name_{}.jpg'.format(storage.uid))
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name

        storage.resource.rename('new_file_name_{}.png'.format(storage.uid))

        yield

        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_exists(self, storage):
        file = storage.resource.get_file()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_source_name,
                type=file.resource.type,
                resource_type=file.resource.resource_type
            )

    def test_new_file_exists(self, storage):
        file = storage.resource.get_file()
        uploader.explicit(
            file.name,
            type=file.resource.type,
            resource_type=file.resource.resource_type
        )

    def test_old_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_file_name_{}{{suffix}}.jpg'.format(storage.uid)),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_file_name_{}{{suffix}}.png'.format(storage.uid)),
            file.name
        )

    def test_basename(self, storage):
        assert storage.resource.basename == utils.get_target_filepath(
            'new_file_name_{}{{suffix}}'.format(storage.uid),
            storage.resource.basename
        )


class TestCloudinaryFileDelete(BacklinkModelTestMixin, TestFileFieldResourceDelete):
    resource_class = CloudinaryFile
    resource_location = 'files/%Y-%m-%d'
    owner_fieldname = 'file'
    owner_model = CloudinaryFileExample

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(NATURE_FILEPATH, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_not_exists(self, storage):
        file_field = storage.resource.get_file_field()
        with pytest.raises(cloudinary.exceptions.Error):
            uploader.explicit(
                storage.old_source_name,
                type=file_field.type,
                resource_type=file_field.resource_type
            )


class TestCloudinaryFileEmpty(TestFileFieldResourceEmpty):
    recource_class = CloudinaryFile

    def test_path(self, storage):
        pass
