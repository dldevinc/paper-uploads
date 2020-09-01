import os
import shutil

import pytest
from django.conf import settings
from django.core.files import File

from app.models import (
    DummyFileFieldResource,
    DummyFileResource,
    DummyImageFieldResource,
    DummyResource,
    DummyVersatileImageResource,
    VariationFile,
)
from paper_uploads import signals
from paper_uploads.variations import PaperVariation

from .. import utils
from ..dummy import *


class TestResource:
    resource_name = 'Nature Tree'

    def _equal_dates(self, date1, date2, delta=5):
        return abs((date2 - date1).seconds) < delta

    @classmethod
    def init(cls, storage):
        storage.resource = DummyResource.objects.create(
            name=cls.resource_name,
            owner_app_label='app',
            owner_model_name='dummyfilefieldresource',
            owner_fieldname='file'
        )
        yield
        storage.resource.delete()

    def test_name(self, storage):
        assert storage.resource.name == self.resource_name

    def test_created_at(self, storage):
        assert self._equal_dates(storage.resource.created_at, storage.now, delta=30)

    def test_modified_at(self, storage):
        assert self._equal_dates(storage.resource.modified_at, storage.now)

    def test_str(self, storage):
        assert str(storage.resource) == self.resource_name

    def test_repr(self, storage):
        assert repr(storage.resource) == "DummyResource('{}')".format(self.resource_name)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name
        }

    def test_get_owner_model(self, storage):
        assert storage.resource.get_owner_model() is DummyFileFieldResource

    def test_get_owner_field(self, storage):
        assert storage.resource.get_owner_field() is DummyFileFieldResource._meta.get_field('file')


class TestWrongResource:
    @staticmethod
    def init(storage):
        storage.wrong_resource = DummyResource.objects.create(
            name='Invalid owner data',
            owner_app_label='app',
            owner_model_name='noexistent',
            owner_fieldname='file'
        )
        yield
        storage.wrong_resource.delete()

    def test_fail_get_owner_model(self, storage):
        assert storage.wrong_resource.get_owner_model() is None

    def test_fail_get_owner_field(self, storage):
        assert storage.wrong_resource.get_owner_field() is None


class TestFileResource(TestResource):
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 28
    resource_hash = '5d8ec227d0d8794d4d99dfbbdb9ad3b479c16952ad4ef69252644d9c404543a5'

    @classmethod
    def init(cls, storage):
        storage.resource = DummyFileResource.objects.create(
            name=cls.resource_name,
            extension=cls.resource_extension,
            size=cls.resource_size,
            owner_app_label='app',
            owner_model_name='dummyfilefieldresource',
            owner_fieldname='file'
        )
        yield
        storage.resource.delete()

    def test_uploaded_at(self, storage):
        assert self._equal_dates(storage.resource.uploaded_at, storage.now)

    def test_extension(self, storage):
        assert storage.resource.extension == self.resource_extension

    def test_size(self, storage):
        assert storage.resource.size == self.resource_size

    def test_content_hash(self, storage):
        assert storage.resource.content_hash == ''

    def test_str(self, storage):
        assert str(storage.resource) == '{}.{}'.format(
            self.resource_name,
            self.resource_extension
        )

    def test_repr(self, storage):
        assert repr(storage.resource) == "{}('{}.{}')".format(
            type(storage.resource).__name__,
            self.resource_name,
            self.resource_extension
        )

    def test_get_basename(self, storage):
        assert storage.resource.get_basename() == '{}.{}'.format(
            self.resource_name,
            self.resource_extension
        )

    def test_get_file_name(self, storage):
        assert storage.resource.get_file_name() == '{}.{}'.format(
            self.resource_name,
            self.resource_extension
        )

    def test_get_file_size(self, storage):
        assert storage.resource.get_file_size() == self.resource_size

    def test_get_file_url(self, storage):
        assert storage.resource.get_file_url() == 'http://example.com/Nature%20Tree.Jpeg'

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'url': 'http://example.com/Nature%20Tree.Jpeg'
        }

    def test_file_exists(self, storage):
        assert storage.resource.file_exists() is True

    def test_get_hash(self, storage):
        with open(NASA_FILEPATH, 'rb') as fp:
            content_hash = storage.resource.get_hash(fp)
        assert content_hash == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

    def test_django_file_get_hash(self, storage):
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp)
            content_hash = storage.resource.get_hash(file)
        assert content_hash == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

    def test_update_hash(self, storage):
        actual_hash = storage.resource.content_hash
        storage.resource.content_hash = ''

        assert storage.resource.update_hash() is True
        assert storage.resource.content_hash == self.resource_hash

        assert storage.resource.update_hash() is False  # not updated
        assert storage.resource.content_hash == self.resource_hash

        storage.resource.content_hash = actual_hash

    def test_attach_file(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert resource.name == 'milky-way-nasa'
        assert resource.extension == 'jpg'
        assert resource.size == 28
        assert resource.content_hash == '5d8ec227d0d8794d4d99dfbbdb9ad3b479c16952ad4ef69252644d9c404543a5'
        assert resource.get_basename() == 'milky-way-nasa.jpg'

        resource.delete_file()

    def test_django_file_attach_file(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp)
            resource.attach_file(file)

        assert resource.name == 'milky-way-nasa'
        assert resource.extension == 'jpg'
        assert resource.size == 28
        assert resource.content_hash == '5d8ec227d0d8794d4d99dfbbdb9ad3b479c16952ad4ef69252644d9c404543a5'

        resource.delete_file()

    def test_named_attach_file(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='overwritten.png')

        assert resource.name == 'overwritten'
        assert resource.extension == 'png'
        assert resource.get_basename() == 'overwritten.png'

        resource.delete_file()

    def test_named_django_file_attach_file(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp, name='overwritten.png')
            resource.attach_file(file)

        assert resource.name == 'overwritten'
        assert resource.extension == 'png'
        assert resource.get_basename() == 'overwritten.png'

        resource.delete_file()

    def test_override_django_file_name_attach_file(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp, name='new name.png')
            resource.attach_file(file, name='override.gif')

        assert resource.name == 'override'
        assert resource.extension == 'gif'
        assert resource.get_basename() == 'override.gif'

        resource.delete_file()

    def test_attach_file_reset_file_position(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
            assert fp.tell() == 0

        resource.delete_file()

    def test_open(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'This'

        # recreate "file" - can't be reopened
        delattr(storage.resource, '_file')
        storage.resource.get_file()

    def test_close(self, storage):
        assert storage.resource.closed is False
        storage.resource.close()
        assert storage.resource.closed is True

        # recreate "file" - can't be reopened
        delattr(storage.resource, '_file')
        storage.resource.get_file()

    def test_proxied_attributes(self, storage):
        storage.resource.seek(0, os.SEEK_END)
        assert storage.resource.tell() == 28
        storage.resource.seek(0)
        assert storage.resource.tell() == 0
        assert storage.resource.read(4) == b'This'
        storage.resource.seek(0)


class TestFileResourceSignals:
    def test_update_hash_signal(self):
        resource = DummyFileResource()
        signal_fired = False
        resource.content_hash = ''

        def signal_handler(sender, instance, content_hash, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource
            assert content_hash == '5d8ec227d0d8794d4d99dfbbdb9ad3b479c16952ad4ef69252644d9c404543a5'

        signals.content_hash_update.connect(signal_handler)

        assert signal_fired is False
        assert resource.update_hash() is True
        assert signal_fired is True

        signals.content_hash_update.disconnect(signal_handler)

    def test_pre_attach_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, file, options, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource

            # ensure instance not filled yet
            assert instance.size == 0
            assert instance.extension == 'jpg'
            assert instance.content_hash == ''

            # ensure file type
            assert isinstance(file, File)

            # ensure original file
            assert file.size == 9711423

            # extra parameters passed to `attach_file`
            assert options == {
                'key1': 'value1',
                'key2': 'value2'
            }

        signals.pre_attach_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            assert signal_fired is False
            resource.attach_file(fp, key1='value1', key2='value2')
            assert signal_fired is True

        resource.delete_file()
        signals.pre_attach_file.disconnect(signal_handler)

    def test_post_signal_fired_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, file, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource

            # ensure instance filled
            assert instance.size == 28
            assert instance.extension == 'jpg'
            assert instance.content_hash == '5d8ec227d0d8794d4d99dfbbdb9ad3b479c16952ad4ef69252644d9c404543a5'

            # ensure file type
            assert isinstance(file, File)

            # ensure modified file
            assert file.size == 28

            # extra parameters passed to `attach_file`
            assert options == {
                'key1': 'value1',
                'key2': 'value2'
            }

            # result of `_attach_file` method
            assert response == {
                'success': True,
            }

        signals.post_attach_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            assert signal_fired is False
            resource.attach_file(fp, key1='value1', key2='value2')
            assert signal_fired is True

        resource.delete_file()
        signals.post_attach_file.disconnect(signal_handler)

    def test_rename_to_same_name(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, **kwargs):
            nonlocal signal_fired
            signal_fired = True

        signals.pre_rename_file.connect(signal_handler)
        signals.post_rename_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert signal_fired is False
        resource.rename_file(os.path.basename(NASA_FILEPATH))
        assert signal_fired is False

        resource.delete_file()
        signals.pre_rename_file.disconnect(signal_handler)
        signals.post_rename_file.disconnect(signal_handler)

    def test_pre_rename_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, old_name, new_name, options, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource
            assert instance.name == 'milky-way-nasa'
            assert instance.extension == 'jpg'
            assert old_name == 'milky-way-nasa.jpg'
            assert new_name == 'new name.png'

            # extra parameters passed to `rename_file`
            assert options == {
                'key1': 'value1',
                'key2': 'value2'
            }

        signals.pre_rename_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert signal_fired is False
        resource.rename_file('new name.png', key1='value1', key2='value2')
        assert signal_fired is True

        resource.delete_file()
        signals.pre_rename_file.disconnect(signal_handler)

    def test_post_rename_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, old_name, new_name, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource
            assert instance.name == 'new name'
            assert instance.extension == 'png'
            assert old_name == 'milky-way-nasa.jpg'
            assert new_name == 'new name.png'

            # extra parameters passed to `rename_file`
            assert options == {
                'key1': 'value1',
                'key2': 'value2'
            }

            # result of `_rename_file` method
            assert response == {
                'success': True,
            }

        signals.post_rename_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert signal_fired is False
        resource.rename_file('new name.png', key1='value1', key2='value2')
        assert signal_fired is True

        resource.delete_file()
        signals.post_rename_file.disconnect(signal_handler)

    def test_pre_delete_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource

        signals.pre_delete_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert signal_fired is False
        resource.delete_file()
        assert signal_fired is True

        signals.pre_delete_file.disconnect(signal_handler)

    def test_post_delete_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource

        signals.post_delete_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert signal_fired is False
        resource.delete_file()
        assert signal_fired is True

        signals.post_delete_file.disconnect(signal_handler)


class TestFileFieldResource(TestFileResource):
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 672759
    resource_hash = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    file_field_name = 'file'

    @classmethod
    def init(cls, storage):
        storage.resource = DummyFileFieldResource(
            owner_app_label='app',
            owner_model_name='dummyfilefieldresource',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_file_field(self, storage):
        assert (
            storage.resource.get_file_field()
            == storage.resource._meta.get_field(self.file_field_name)
        )

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'file_field/Nature_Tree{suffix}.Jpeg',
            file_name
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url == utils.get_target_filepath(
            '/media/file_field/Nature_Tree{suffix}.Jpeg',
            file_url
        )

    def test_open(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'\xff\xd8\xff\xe0'

        storage.resource.open()  # reopen

    def test_close(self, storage):
        assert storage.resource.closed is False
        storage.resource.close()
        assert storage.resource.closed is True

        storage.resource.open()  # reopen

    def test_proxied_attributes(self, storage):
        storage.resource.seek(0, os.SEEK_END)
        assert storage.resource.tell() == self.resource_size
        storage.resource.seek(0)
        assert storage.resource.tell() == 0
        storage.resource.seek(0)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'url': utils.get_target_filepath(
                '/media/file_field/Nature_Tree{suffix}.Jpeg',
                storage.resource.get_file_url()
            )
        }

    def test_content_hash(self, storage):
        assert storage.resource.content_hash == self.resource_hash

    def test_path(self, storage):
        assert storage.resource.path.endswith(utils.get_target_filepath(
            '/media/file_field/Nature_Tree{suffix}.Jpeg',
            storage.resource.get_file_url()
        ))

    def test_url(self, storage):
        assert storage.resource.url == utils.get_target_filepath(
            '/media/file_field/Nature_Tree{suffix}.Jpeg',
            storage.resource.get_file_url()
        )


class TestRenameFile:
    def test_rename_file(self):
        resource = DummyFileFieldResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='old_name.jpg')

        old_source_path = resource.file.path
        assert os.path.exists(old_source_path) is True

        resource.rename_file('new_name.png')

        # ensure old file still exists
        assert os.path.exists(old_source_path) is True
        assert os.path.exists(resource.file.path) is True

        assert resource.get_file_name() == 'file_field/new_name.png'

        os.remove(old_source_path)
        resource.delete_file()


class TestDeleteFile:
    def test_delete_file(self):
        resource = DummyFileFieldResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        source_path = resource.file.path
        assert os.path.exists(source_path) is True

        resource.delete_file()
        assert os.path.exists(source_path) is False


class TestEmptyFileFieldResource:
    @classmethod
    def init(cls, storage):
        storage.resource = DummyFileFieldResource()
        yield

    def test_open(self, storage):
        with pytest.raises(ValueError):
            storage.resource.open()  # noqa

    def test_closed(self, storage):
        assert storage.resource.closed is True

    def test_read(self, storage):
        with pytest.raises(ValueError):
            storage.resource.read()  # noqa

    def test_url(self, storage):
        with pytest.raises(ValueError):
            storage.resource.url  # noqa

    def test_path(self, storage):
        with pytest.raises(ValueError):
            storage.resource.path  # noqa

    def test_get_file(self, storage):
        assert bool(storage.resource.get_file()) is False

    def test_get_file_name(self, storage):
        with pytest.raises(ValueError):
            storage.resource.get_file_name()

    def test_get_file_size(self, storage):
        with pytest.raises(ValueError):
            storage.resource.get_file_size()

    def test_get_file_url(self, storage):
        with pytest.raises(ValueError):
            storage.resource.get_file_url()

    def test_file_exists(self, storage):
        assert storage.resource.file_exists() is False

    def test_rename_file(self, storage):
        with pytest.raises(ValueError):
            storage.resource.rename_file('bla-bla.jpg')

    def test_delete_file(self, storage):
        with pytest.raises(ValueError):
            storage.resource.delete_file()


class TestImageFieldResource(TestFileFieldResource):
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_hash = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    file_field_name = 'image'

    @classmethod
    def init(cls, storage):
        storage.resource = DummyImageFieldResource(
            title='Calliphora',
            description='Calliphora is a genus of blow flies, also known as bottle flies',
            owner_app_label='app',
            owner_model_name='dummyversatileimageresource',
            owner_fieldname='file'
        )

        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'image_field/Nature_Tree{suffix}.jpg',
            file_name
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url == utils.get_target_filepath(
            '/media/image_field/Nature_Tree{suffix}.jpg',
            file_url
        )

    def test_path(self, storage):
        assert storage.resource.path.endswith(utils.get_target_filepath(
            '/media/image_field/Nature_Tree{suffix}.jpg',
            storage.resource.get_file_url()
        ))

    def test_url(self, storage):
        assert storage.resource.url == utils.get_target_filepath(
            '/media/image_field/Nature_Tree{suffix}.jpg',
            storage.resource.get_file_url()
        )

    def test_get_owner_model(self, storage):
        assert storage.resource.get_owner_model() is DummyVersatileImageResource

    def test_get_owner_field(self, storage):
        assert storage.resource.get_owner_field() is DummyVersatileImageResource._meta.get_field('file')

    def test_title(self, storage):
        assert storage.resource.title == 'Calliphora'

    def test_description(self, storage):
        assert storage.resource.description == 'Calliphora is a genus of blow flies, ' \
                                               'also known as bottle flies'

    def test_width(self, storage):
        assert storage.resource.width == 1534

    def test_height(self, storage):
        assert storage.resource.height == 2301

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
            'url': utils.get_target_filepath(
                '/media/image_field/Nature_Tree{suffix}.jpg',
                storage.resource.get_file_url()
            ),
        }


class TestVariationFile:
    @staticmethod
    def init(storage):
        storage.resource = DummyVersatileImageResource(
            owner_app_label='app',
            owner_model_name='dummyversatileimageresource',
            owner_fieldname='file'
        )
        with open(NASA_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        storage.file = VariationFile(storage.resource, 'desktop')

        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_name(self, storage):
        assert storage.file.name == utils.get_target_filepath(
            'versatile_image/milky-way-nasa{suffix}.desktop.jpg',
            storage.resource.get_file_name()
        )

    def test_instance(self, storage):
        assert isinstance(storage.file.instance, DummyVersatileImageResource)
        assert storage.file.instance is storage.resource

    def test_variation_name(self, storage):
        assert storage.file.variation_name == 'desktop'

    def test_size(self, storage):
        assert storage.file.size == 115559

    def test_variation(self, storage):
        assert isinstance(storage.file.variation, PaperVariation)
        assert storage.file.variation.name == 'desktop'

    def test_path(self, storage):
        assert storage.resource.path.endswith(utils.get_target_filepath(
            '/media/versatile_image/milky-way-nasa{suffix}.jpg',
            storage.resource.get_file_url()
        ))

    def test_url(self, storage):
        assert storage.resource.url == utils.get_target_filepath(
            '/media/versatile_image/milky-way-nasa{suffix}.jpg',
            storage.resource.get_file_url()
        )

    def test_exists(self, storage):
        assert storage.file.exists() is True

    def test_width(self, storage):
        assert storage.file.width == 800

    def test_height(self, storage):
        assert storage.file.height == 577

    def test_open(self, storage):
        assert storage.file.closed is True
        with storage.file.open():
            assert storage.file.closed is False
        assert storage.file.closed is True

    def test_delete(self, storage):
        source_name = storage.file.name
        source_file = storage.file.path
        backup_file = os.path.join(settings.BASE_DIR, 'media/versatile_image/nasa.bak.jpg')
        shutil.copyfile(source_file, backup_file)

        storage.file.delete()
        assert storage.file.exists() is False

        with pytest.raises(ValueError):
            x = storage.file.path

        with pytest.raises(ValueError):
            x = storage.file.url

        with pytest.raises(ValueError):
            x = storage.file.size

        with pytest.raises(ValueError):
            storage.file.open()

        assert storage.file.exists() is False

        storage.file.name = source_name
        shutil.move(backup_file, source_file)

    def test_delete_unexisted(self, storage):
        source_name = storage.file.name
        source_file = storage.file.path
        backup_file = os.path.join(settings.BASE_DIR, 'media/versatile_image/nasa.bak.jpg')
        shutil.copyfile(source_file, backup_file)

        storage.file.delete()
        assert storage.file.exists() is False

        # call again
        storage.file.delete()

        storage.file.name = source_name
        shutil.move(backup_file, source_file)


class TestVersatileImageResource(TestImageFieldResource):
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_hash = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    file_field_name = 'file'

    @classmethod
    def init(cls, storage):
        storage.resource = DummyVersatileImageResource(
            title='Calliphora',
            description='Calliphora is a genus of blow flies, also known as bottle flies',
            owner_app_label='app',
            owner_model_name='dummyversatileimageresource',
            owner_fieldname='file'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'versatile_image/Nature_Tree{suffix}.jpg',
            file_name
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url == utils.get_target_filepath(
            '/media/versatile_image/Nature_Tree{suffix}.jpg',
            file_url
        )

    def test_path(self, storage):
        assert storage.resource.path.endswith(utils.get_target_filepath(
            '/media/versatile_image/Nature_Tree{suffix}.jpg',
            storage.resource.get_file_url()
        ))

    def test_url(self, storage):
        assert storage.resource.url == utils.get_target_filepath(
            '/media/versatile_image/Nature_Tree{suffix}.jpg',
            storage.resource.get_file_url()
        )

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
            'url': utils.get_target_filepath(
                '/media/versatile_image/Nature_Tree{suffix}.jpg',
                storage.resource.get_file_url()
            ),
        }

    def test_get_variations(self, storage):
        variations = storage.resource.get_variations()
        assert len(variations) == 2
        assert set(variations.keys()) == {'desktop', 'mobile'}
        assert all(isinstance(v, PaperVariation) for v in variations.values()) is True

    def test_get_variation_file(self, storage):
        vfile = storage.resource.get_variation_file('desktop')
        assert isinstance(vfile, VariationFile)
        assert vfile.exists() is True
        assert vfile.path.endswith(
            utils.get_target_filepath(
                'Nature_Tree{suffix}.desktop.jpg',
                storage.resource.get_file_url()
            ),
        )

    def test_nonexisted_get_variation_file(self, storage):
        with pytest.raises(KeyError):
            storage.resource.get_variation_file('something')

    def test_variation_files(self, storage):
        assert dict(storage.resource.variation_files()) == {
            'desktop': storage.resource.desktop,
            'mobile': storage.resource.mobile,
        }

    def test_variation_attribute(self, storage):
        assert isinstance(storage.resource.desktop, VariationFile)
        assert isinstance(storage.resource.mobile, VariationFile)

        with pytest.raises(AttributeError):
            storage.resource.tablet  # noqa

    def test_variation_files_exists(self, storage):
        assert os.path.exists(storage.resource.file.path) is True
        assert os.path.exists(storage.resource.desktop.path) is True
        assert os.path.exists(storage.resource.mobile.path) is True

    def test_calculate_max_size(self, storage):
        assert storage.resource.calculate_max_size((3000, 2000)) == (900, 600)
        assert storage.resource.calculate_max_size((2000, 3000)) == (800, 1200)


@pytest.mark.django_db
class TestImageResourceVariations:
    def test_variation_attributes_after_delete(self):
        resource = DummyVersatileImageResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.delete_file()

        with pytest.raises(AttributeError):
            resource.desktop  # noqa

    def test_variation_files_after_delete(self):
        resource = DummyVersatileImageResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.delete_file()

        assert list(resource.variation_files()) == []

    def test_reattach_file(self):
        resource = DummyVersatileImageResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='initial.jpg')

        assert resource.desktop.name == 'versatile_image/initial.desktop.jpg'
        assert resource._variation_files_cache == {
            'desktop': resource.desktop,
            'mobile': resource.mobile,
        }

        os.remove(resource.file.path)
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='reattached.jpg')

        assert resource.desktop.name == 'versatile_image/reattached.desktop.jpg'
        assert resource._variation_files_cache == {
            'desktop': resource.desktop,
            'mobile': resource.mobile,
        }

        resource.delete_file()

    def test_delete_file(self):
        resource = DummyVersatileImageResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        source_path = resource.file.path
        desktop_path = resource.desktop.path
        mobile_path = resource.mobile.path

        assert os.path.exists(source_path) is True
        assert os.path.exists(desktop_path) is True
        assert os.path.exists(mobile_path) is True

        resource.delete_file()

        # ensure variations also deleted
        assert os.path.exists(source_path) is False
        assert os.path.exists(desktop_path) is False
        assert os.path.exists(mobile_path) is False

        resource.delete()

    def test_rename_file(self):
        resource = DummyVersatileImageResource()
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        old_source_path = resource.file.path
        old_desktop_path = resource.desktop.path
        old_mobile_path = resource.mobile.path

        assert os.path.exists(old_source_path) is True
        assert os.path.exists(old_desktop_path) is True
        assert os.path.exists(old_mobile_path) is True

        resource.rename_file('renamed.jpg')

        # ensure previous files still exists
        assert os.path.exists(old_source_path) is True
        assert os.path.exists(old_desktop_path) is True
        assert os.path.exists(old_mobile_path) is True

        assert os.path.exists(resource.file.path) is True
        assert os.path.exists(resource.desktop.path) is True
        assert os.path.exists(resource.mobile.path) is True

        resource.delete_file()

        os.remove(old_source_path)
        os.remove(old_desktop_path)
        os.remove(old_mobile_path)

        resource.delete()

    def test_recut(self):
        resource = DummyVersatileImageResource()
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        os.remove(resource.desktop.path)
        os.remove(resource.mobile.path)

        assert os.path.exists(resource.file.path) is True
        assert os.path.exists(resource.desktop.path) is False
        assert os.path.exists(resource.mobile.path) is False

        resource.recut('mobile')

        assert os.path.exists(resource.file.path) is True
        assert os.path.exists(resource.desktop.path) is False
        assert os.path.exists(resource.mobile.path) is True

        resource.delete_file()
        resource.delete()

    def test_recut_missing_source(self):
        resource = DummyVersatileImageResource()
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        os.remove(resource.file.path)
        os.remove(resource.desktop.path)

        with pytest.raises(FileNotFoundError):
            resource.recut('desktop')

        resource.delete_file()
        resource.delete()

    def test_variation_created_signal(self):
        resource = DummyVersatileImageResource()
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        signal_fired_times = 0
        signals_fired = {
            'desktop': False,
            'mobile': False,
        }

        def signal_handler(sender, instance, file, **kwargs):
            nonlocal signal_fired_times
            nonlocal signals_fired
            signal_fired_times += 1
            signals_fired[file.variation_name] = True
            assert sender is DummyVersatileImageResource
            assert instance is resource
            assert isinstance(file, VariationFile)

        signals.variation_created.connect(signal_handler)

        resource.save()

        assert signal_fired_times == 2
        assert signals_fired == {
            'desktop': True,
            'mobile': True,
        }

        resource.delete_file()
        resource.delete()
        signals.variation_created.disconnect(signal_handler)


class TestEmptyVersatileImageResource(TestEmptyFileFieldResource):
    @classmethod
    def init(cls, storage):
        storage.resource = DummyVersatileImageResource()
        yield

    def test_variation_files(self, storage):
        assert list(storage.resource.variation_files()) == []

    def test_variation_attribute(self, storage):
        with pytest.raises(AttributeError):
            storage.resource.desktop  # noqa
