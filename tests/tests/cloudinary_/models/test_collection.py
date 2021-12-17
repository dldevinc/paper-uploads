import posixpath
from contextlib import contextmanager

import cloudinary.exceptions
import pytest
from cloudinary import uploader
from django.core.files import File
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from app.models.site import (
    CloudinaryCompleteCollection,
    CloudinaryFileCollection,
    CloudinaryMediaCollection,
)
from paper_uploads import exceptions
from paper_uploads.cloudinary.models import (
    CloudinaryFileItem,
    CloudinaryImageItem,
    CloudinaryMediaItem,
)

from ... import utils
from ...dummy import *
from ...models.test_collection import CollectionItemMixin
from ...models.test_dummy import (
    TestFileFieldResourceAttach,
    TestFileFieldResourceDelete,
    TestFileFieldResourceEmpty,
    TestFileFieldResourceRename,
    TestImageFieldResourceAttach,
    TestImageFieldResourceDelete,
    TestImageFieldResourceEmpty,
    TestImageFieldResourceRename,
)
from .test_base import CloudinaryFileResource


class TestFileItem(CollectionItemMixin, CloudinaryFileResource):
    resource_url = '/media/collections/files/%Y-%m-%d'
    resource_location = 'collections/files/%Y-%m-%d'
    resource_name = 'table'
    resource_extension = 'xls'
    resource_size = 8704
    resource_checksum = 'c9c8ad905aa5142731b1e8ab34d5862f871627fa7ad8005264494c2489d2061e'
    file_field_name = 'file'
    collection_class = CloudinaryCompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = CloudinaryFileItem()
        storage.resource.attach_to(storage.collection)
        with open(EXCEL_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_item_type(self, storage):
        assert storage.resource.type == 'file'

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == 'private'
        assert file_field.resource_type == 'raw'

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        pattern = posixpath.join(self.resource_location, 'table{suffix}.xls')
        assert public_id == utils.get_target_filepath(pattern, public_id)

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'table{suffix}.xls')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'\xd0\xcf\x11\xe0'

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'itemType': 'file',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'caption': '{}.{}'.format(
                self.resource_name,
                self.resource_extension
            ),
            'size': self.resource_size,
            'order': 0,
            'preview': render_to_string(
                'paper_uploads/items/preview/file.html',
                storage.resource.get_preview_context()
            ),
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_accept(self, storage):
        with open(EXCEL_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True


@pytest.mark.django_db
class TestFileItemAttach(TestFileFieldResourceAttach):
    resource_class = CloudinaryFileItem
    collection_class = CloudinaryFileCollection

    @contextmanager
    def get_resource(self):
        collection = self.collection_class.objects.create()
        resource = self.resource_class()
        resource.attach_to(collection)
        try:
            yield resource
        finally:
            resource.delete_file()
            collection.delete()


class TestFileItemRename(TestFileFieldResourceRename):
    resource_class = CloudinaryFileItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = CloudinaryFileCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.uid = get_random_string(5)
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_cfile_name_{}.jpg'.format(storage.uid))
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.resource.rename('new_cfile_name_{}.png'.format(storage.uid))

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
            posixpath.join(self.resource_location, 'old_cfile_name_{}{{suffix}}.jpg'.format(storage.uid)),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_cfile_name_{}{{suffix}}.png'.format(storage.uid)),
            file.name
        )

    def test_basename(self, storage):
        assert storage.resource.basename == utils.get_target_filepath(
            'new_cfile_name_{}{{suffix}}'.format(storage.uid),
            storage.resource.basename
        )


class TestFileItemDelete(TestFileFieldResourceDelete):
    resource_class = CloudinaryFileItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = CloudinaryFileCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
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


class TestFileItemEmpty(TestFileFieldResourceEmpty):
    recource_class = CloudinaryFileItem
    collection_class = CloudinaryFileCollection

    @classmethod
    def init_class(cls, storage):
        collection = cls.collection_class.objects.create()
        storage.resource = cls.recource_class()
        storage.resource.attach_to(collection)
        yield
        collection.delete()

    def test_path(self, storage):
        pass


class TestMediaItem(CollectionItemMixin, CloudinaryFileResource):
    resource_url = '/media/collections/files/%Y-%m-%d'
    resource_location = 'collections/files/%Y-%m-%d'
    resource_name = 'audio'
    resource_extension = 'mp3'
    resource_size = 2113939
    resource_checksum = '4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d'
    owner_app_label = ''
    owner_model_name = ''
    owner_fieldname = ''
    owner_model = None
    file_field_name = 'file'
    collection_class = CloudinaryCompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = CloudinaryMediaItem()
        storage.resource.attach_to(storage.collection)
        with open(AUDIO_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_item_type(self, storage):
        assert storage.resource.type == 'media'

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == 'private'
        assert file_field.resource_type == 'video'

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        pattern = posixpath.join(self.resource_location, 'audio{suffix}')
        assert public_id == utils.get_target_filepath(pattern, public_id)

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'audio{suffix}')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'ID3\x03'

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'itemType': 'media',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'caption': '{}.{}'.format(
                self.resource_name,
                self.resource_extension
            ),
            'size': self.resource_size,
            'order': 0,
            'preview': render_to_string(
                'paper_uploads/items/preview/file.html',
                storage.resource.get_preview_context()
            ),
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_accept(self, storage):
        with open(EXCEL_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True


@pytest.mark.django_db
class TestMediaItemAttach(TestFileFieldResourceAttach):
    resource_class = CloudinaryMediaItem
    resource_size = 2113939
    resource_checksum = '4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d'
    collection_class = CloudinaryMediaCollection

    @contextmanager
    def get_resource(self):
        collection = self.collection_class.objects.create()
        resource = self.resource_class()
        resource.attach_to(collection)
        try:
            yield resource
        finally:
            resource.delete_file()
            collection.delete()

    def test_file(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp)

            assert resource.basename == 'audio'
            assert resource.extension == 'mp3'
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_django_file(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                file = File(fp, name='milky-way-nasa.jpg')
                resource.attach(file)

            assert resource.basename == 'milky-way-nasa'
            assert resource.extension == 'mp3'
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_override_name(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp, name='overwritten.jpg')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'mp3'

    def test_override_django_name(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                file = File(fp, name='not_used.png')
                resource.attach(file, name='overwritten.jpg')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'mp3'

    def test_wrong_extension(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp, name='overwritten.gif')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'mp3'

    def test_file_position_at_end(self):
        with self.get_resource() as resource:
            with open(AUDIO_FILEPATH, 'rb') as fp:
                resource.attach(fp)
                assert fp.tell() == self.resource_size

    def test_unsupported_file(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                with pytest.raises(exceptions.UnsupportedResource):
                    resource.attach(fp)


class TestMediaItemRename(TestFileFieldResourceRename):
    resource_class = CloudinaryMediaItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = CloudinaryMediaCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.uid = get_random_string(5)
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(AUDIO_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_cmedia_name_{}.mp3'.format(storage.uid))
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.resource.rename('new_cmedia_name_{}.ogg'.format(storage.uid))

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
            posixpath.join(self.resource_location, 'old_cmedia_name_{}{{suffix}}'.format(storage.uid)),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_cmedia_name_{}{{suffix}}'.format(storage.uid)),
            file.name
        )

    def test_basename(self, storage):
        assert storage.resource.basename == utils.get_target_filepath(
            'new_cmedia_name_{}{{suffix}}'.format(storage.uid),
            storage.resource.basename
        )

    def test_extension(self, storage):
        assert storage.resource.extension == 'mp3'


class TestMediaItemDelete(TestFileFieldResourceDelete):
    resource_class = CloudinaryMediaItem
    resource_location = 'collections/files/%Y-%m-%d'
    collection_class = CloudinaryMediaCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(AUDIO_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}'),
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


class TestMediaItemEmpty(TestFileFieldResourceEmpty):
    recource_class = CloudinaryMediaItem
    collection_class = CloudinaryMediaCollection

    @classmethod
    def init_class(cls, storage):
        collection = cls.collection_class.objects.create()
        storage.resource = cls.recource_class()
        storage.resource.attach_to(collection)
        yield
        collection.delete()

    def test_path(self, storage):
        pass


class TestImageItem(CollectionItemMixin, CloudinaryFileResource):
    resource_url = 'collections/images/%Y-%m-%d'
    resource_location = 'collections/images/%Y-%m-%d'
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = ''
    owner_model_name = ''
    owner_fieldname = ''
    owner_model = None
    file_field_name = 'file'
    collection_class = CloudinaryCompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = CloudinaryImageItem()
        storage.resource.attach_to(storage.collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == self.resource_location

    def test_item_type(self, storage):
        assert storage.resource.type == 'image'

    def test_type(self, storage):
        file_field = storage.resource.get_file_field()
        assert file_field.type == 'private'
        assert file_field.resource_type == 'image'

    def test_public_id(self, storage):
        public_id = storage.resource.get_file().public_id
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}')
        assert public_id == utils.get_target_filepath(pattern, public_id)

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'itemType': 'image',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'caption': '{}.{}'.format(
                self.resource_name,
                self.resource_extension
            ),
            'size': self.resource_size,
            'width': 1534,
            'height': 2301,
            'cropregion': '',
            'title': '',
            'description': '',
            'order': 0,
            'preview': render_to_string(
                'paper_uploads_cloudinary/items/preview/image.html',
                storage.resource.get_preview_context()
            ),
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_width(self, storage):
        assert storage.resource.width == 1534

    def test_height(self, storage):
        assert storage.resource.height == 2301

    def test_accept(self, storage):
        with open(EXCEL_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False

        with open(NATURE_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(MEDITATION_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is True

        with open(AUDIO_FILEPATH, 'rb') as fp:
            assert storage.resource.accept(File(fp)) is False


@pytest.mark.django_db
class TestImageItemAttach(TestImageFieldResourceAttach):
    resource_class = CloudinaryImageItem
    collection_class = CloudinaryCompleteCollection

    @contextmanager
    def get_resource(self):
        collection = self.collection_class.objects.create()
        resource = self.resource_class()
        resource.attach_to(collection)
        try:
            yield resource
        finally:
            resource.delete_file()
            collection.delete()

    def test_unsupported_file(self):
        with self.get_resource() as resource:
            with open(EXCEL_FILEPATH, 'rb') as fp:
                with pytest.raises(exceptions.UnsupportedResource):
                    resource.attach(fp)


class TestImageItemRename(TestImageFieldResourceRename):
    resource_class = CloudinaryImageItem
    resource_location = 'collections/images/%Y-%m-%d'
    collection_class = CloudinaryCompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.uid = get_random_string(5)
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_cimage_name_{}.jpg'.format(storage.uid))
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.resource.rename('new_cimage_name_{}.png'.format(storage.uid))

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
            posixpath.join(self.resource_location, 'old_cimage_name_{}{{suffix}}'.format(storage.uid)),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_cimage_name_{}{{suffix}}'.format(storage.uid)),
            file.name
        )

    def test_basename(self, storage):
        assert storage.resource.basename == utils.get_target_filepath(
            'new_cimage_name_{}{{suffix}}'.format(storage.uid),
            storage.resource.basename
        )

    def test_extension(self, storage):
        assert storage.resource.extension == 'jpg'


class TestImageItemDelete(TestImageFieldResourceDelete):
    resource_class = CloudinaryImageItem
    resource_location = 'collections/images/%Y-%m-%d'
    collection_class = CloudinaryCompleteCollection

    @classmethod
    def init_class(cls, storage):
        storage.collection = cls.collection_class.objects.create()
        storage.resource = cls.resource_class()
        storage.resource.attach_to(storage.collection)
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            storage.resource.attach(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}'),
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


class TestImageItemEmpty(TestImageFieldResourceEmpty):
    recource_class = CloudinaryImageItem
    collection_class = CloudinaryCompleteCollection

    @classmethod
    def init_class(cls, storage):
        collection = cls.collection_class.objects.create()
        storage.resource = cls.recource_class()
        storage.resource.attach_to(collection)
        yield
        collection.delete()

    def test_path(self, storage):
        pass
