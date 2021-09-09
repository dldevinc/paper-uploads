import os
import posixpath
import math
from contextlib import contextmanager

import pytest
from django.core.files import File
from django.db.models.fields import Field

from app.models import (
    DummyFileFieldResource,
    DummyFileResource,
    DummyImageFieldResource,
    DummyResource,
    DummyVersatileImageResource,
)
from paper_uploads import signals
from paper_uploads.files import VariationFile
from paper_uploads.variations import PaperVariation

from .. import utils
from ..dummy import *


class BacklinkModelMixin:
    owner_app_label = 'app'
    owner_model_name = 'model'
    owner_fieldname = 'field'
    owner_class = None

    @classmethod
    def init_class(cls, storage):
        pass

    def test_owner_app_label(self, storage):
        assert storage.resource.owner_app_label == self.owner_app_label

    def test_owner_model_name(self, storage):
        assert storage.resource.owner_model_name == self.owner_model_name

    def test_owner_fieldname(self, storage):
        assert storage.resource.owner_fieldname == self.owner_fieldname

    def test_get_owner_model(self, storage):
        assert storage.resource.get_owner_model() is self.owner_class

    def test_get_owner_field(self, storage):
        assert isinstance(storage.resource.get_owner_field(), Field)


class TestInvalidBacklinkModelMixin:
    def test_empty_app(self):
        obj = DummyResource(
            owner_model_name='dummyfilefieldresource',
            owner_fieldname='file'
        )
        assert obj.get_owner_model() is None
        assert obj.get_owner_field() is None

    def test_empty_model(self):
        obj = DummyResource(
            owner_app_label='app',
            owner_fieldname='file'
        )
        assert obj.get_owner_model() is None
        assert obj.get_owner_field() is None

    def test_empty_field(self):
        obj = DummyResource(
            owner_app_label='app',
            owner_model_name='dummyfilefieldresource',
        )
        assert obj.get_owner_model() is DummyFileFieldResource
        assert obj.get_owner_field() is None

    def test_invalid_model(self):
        obj = DummyResource(
            owner_app_label='app',
            owner_model_name='nooooo',
            owner_fieldname='file'
        )
        assert obj.get_owner_model() is None
        assert obj.get_owner_field() is None

    def test_invalid_field(self):
        obj = DummyResource(
            owner_app_label='app',
            owner_model_name='dummyfilefieldresource',
            owner_fieldname='nooooo'
        )
        assert obj.get_owner_model() is DummyFileFieldResource
        assert obj.get_owner_field() is None


class TestResource(BacklinkModelMixin):
    owner_app_label = 'app'
    owner_model_name = 'dummyfilefieldresource'
    owner_fieldname = 'file'
    owner_class = DummyFileFieldResource

    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyResource.objects.create(
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        yield
        storage.resource.delete()

    def _equal_dates(self, date1, date2, delta=5):
        return abs((date2 - date1).seconds) < delta

    def test_created_at(self, storage):
        # `created_at` is set before file upload. So, it can be mush lesser then `storage.now`.
        assert self._equal_dates(storage.resource.created_at, storage.now, delta=30)

    def test_modified_at(self, storage):
        assert self._equal_dates(storage.resource.modified_at, storage.now)

    def test_created_at_less_than_modified_at(self, storage):
        assert storage.resource.created_at < storage.resource.modified_at

    def test_repr(self, storage):
        assert repr(storage.resource) == "{} #{}".format(
            type(storage.resource).__name__,
            storage.resource.pk
        )

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
        }


class TestFileResource(TestResource):
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 28
    resource_checksum = '5d8ec227d0d8794d4d99dfbbdb9ad3b479c16952ad4ef69252644d9c404543a5'
    owner_app_label = 'app'
    owner_model_name = 'dummyfilefieldresource'
    owner_fieldname = 'file'
    owner_class = DummyFileFieldResource

    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyFileResource.objects.create(
            basename=cls.resource_name,
            extension=cls.resource_extension,
            size=cls.resource_size,
            owner_app_label=cls.owner_app_label,
            owner_model_name=cls.owner_model_name,
            owner_fieldname=cls.owner_fieldname
        )
        storage.resource.update_checksum()
        yield
        storage.resource.delete()

    def test_name(self, storage):
        assert storage.resource.name == '{}.{}'.format(
            self.resource_name,
            self.resource_extension
        )

    def test_basename(self, storage):
        assert storage.resource.basename == self.resource_name

    def test_extension(self, storage):
        assert storage.resource.extension == self.resource_extension

    def test_size(self, storage):
        assert storage.resource.size == self.resource_size

    def test_checksum(self, storage):
        assert storage.resource.checksum == self.resource_checksum

    def test_uploaded_at(self, storage):
        assert self._equal_dates(storage.resource.uploaded_at, storage.now)
        assert self._equal_dates(storage.resource.uploaded_at, storage.resource.modified_at)

    def test_str(self, storage):
        assert str(storage.resource) == storage.resource.get_basename()

    def test_repr(self, storage):
        assert repr(storage.resource) == "{}('{}')".format(
            type(storage.resource).__name__,
            storage.resource.get_basename()
        )

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'url': 'http://example.com/Nature%20Tree.Jpeg',
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_update_checksum(self, storage):
        storage.resource.checksum = ''

        assert storage.resource.update_checksum() is True
        assert storage.resource.checksum == self.resource_checksum

        assert storage.resource.update_checksum() is False  # not updated
        assert storage.resource.checksum == self.resource_checksum

    def test_get_basename(self, storage):
        assert storage.resource.get_basename() == '{}.{}'.format(
            self.resource_name,
            self.resource_extension
        )

    def test_get_file_size(self, storage):
        assert storage.resource.get_file_size() == self.resource_size

    def test_get_file_url(self, storage):
        assert storage.resource.get_file_url() == 'http://example.com/Nature%20Tree.Jpeg'

    def test_file_exists(self, storage):
        assert storage.resource.file_exists() is True

    def test_prepare_file(self, storage):
        obj = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp)
            assert obj._prepare_file(file) is file

    @pytest.mark.skip(reason="abstract method")
    def test_get_file_field(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_closed(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_open(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_reopen(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_reopen_reset_position(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_read(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_close(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_reclose(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_seekable(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_readable(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_writable(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_seek(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_tell(self, storage):
        raise NotImplementedError

    @pytest.mark.skip(reason="abstract method")
    def test_chunks(self, storage):
        raise NotImplementedError


class TestFileResourceSignals:
    def test_update_checksum_signal(self):
        resource = DummyFileResource()
        signal_fired = False
        resource.checksum = ''

        def signal_handler(sender, instance, checksum, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource
            assert checksum == '5d8ec227d0d8794d4d99dfbbdb9ad3b479c16952ad4ef69252644d9c404543a5'

        signals.checksum_update.connect(signal_handler)

        assert signal_fired is False
        assert resource.update_checksum() is True
        assert signal_fired is True

        signals.checksum_update.disconnect(signal_handler)

    def test_pre_attach_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, file, options, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource

            # ensure instance not filled yet
            assert instance.basename == ''
            assert instance.extension == ''
            assert instance.size == 0
            assert instance.checksum == ''

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

    def test_post_attach_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, file, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource

            # ensure instance filled
            assert instance.basename == 'milky-way-nasa'
            assert instance.extension == 'jpg'
            assert instance.size == 28
            assert instance.checksum == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

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
        pre_signal_fired = False
        post_signal_fired = False

        def pre_signal_handler(sender, **kwargs):
            nonlocal pre_signal_fired
            pre_signal_fired = True

        def post_signal_handler(sender, **kwargs):
            nonlocal post_signal_fired
            post_signal_fired = True

        signals.pre_rename_file.connect(pre_signal_handler)
        signals.post_rename_file.connect(post_signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        orig_name = resource.name
        orig_basename = resource.basename

        assert pre_signal_fired is False
        assert post_signal_fired is False
        resource.rename_file(os.path.basename(NASA_FILEPATH))
        assert pre_signal_fired is True
        assert post_signal_fired is True

        assert orig_name == resource.name
        assert orig_basename == resource.basename

        resource.delete_file()
        signals.pre_rename_file.disconnect(pre_signal_handler)
        signals.post_rename_file.disconnect(post_signal_handler)

    def test_pre_rename_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, old_name, new_name, options, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource
            assert instance.basename == 'milky-way-nasa'
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
            assert instance.basename == 'new name'
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

        def signal_handler(sender, instance, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource

            # extra parameters passed to `rename_file`
            assert options == {
                'key1': 'value1',
                'key2': 'value2'
            }

            # result of `_delete_file` method
            assert response == {
                'success': True,
            }

        signals.post_delete_file.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        assert signal_fired is False
        resource.delete_file(key1='value1', key2='value2')
        assert signal_fired is True

        signals.post_delete_file.disconnect(signal_handler)


class TestFileFieldResource(TestFileResource):
    resource_url = '/media/file_field'
    resource_location = 'file_field'
    resource_name = 'Nature Tree'
    resource_extension = 'Jpeg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = 'app'
    owner_model_name = 'dummyfilefieldresource'
    owner_fieldname = 'file'
    owner_class = DummyFileFieldResource
    file_field_name = 'file'

    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyFileFieldResource(
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

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}.Jpeg')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_get_file_folder(self, storage):
        assert storage.resource.get_file_folder() == ""

    def test_get_file_field(self, storage):
        assert (
            storage.resource.get_file_field()
            == storage.resource._meta.get_field(self.file_field_name)
        )

    def test_closed(self, storage):
        with storage.resource.open():
            assert storage.resource.closed is False
        assert storage.resource.closed is True

    def test_open(self, storage):
        with storage.resource.open() as fp:
            assert fp is storage.resource
            assert fp._FileProxyMixin__file is storage.resource.get_file()

    def test_reopen(self, storage):
        with storage.resource.open() as opened:
            with storage.resource.open() as reopened:
                assert opened is reopened
                assert opened._FileProxyMixin__file is opened._FileProxyMixin__file

    def test_reopen_reset_position(self, storage):
        with storage.resource.open():
            storage.resource.read(4)  # change file position
            assert storage.resource.tell() == 4

            with storage.resource.open():
                assert storage.resource.tell() == 0

    def test_read(self, storage):
        with storage.resource.open():
            assert storage.resource.read(4) == b'\xff\xd8\xff\xe0'

    def test_close(self, storage):
        with storage.resource.open():
            assert storage.resource._FileProxyMixin__file is not None
        assert storage.resource._FileProxyMixin__file is None

    def test_reclose(self, storage):
        with storage.resource.open():
            pass
        return storage.resource.close()

    def test_seekable(self, storage):
        with storage.resource.open() as fp:
            assert fp.seekable() is True

    def test_readable(self, storage):
        with storage.resource.open() as fp:
            assert fp.readable() is True

    def test_writable(self, storage):
        with storage.resource.open() as fp:
            assert fp.writable() is False

    def test_seek(self, storage):
        with storage.resource.open() as fp:
            fp.seek(0, os.SEEK_END)
            assert fp.tell() == self.resource_size

    def test_tell(self, storage):
        with storage.resource.open() as fp:
            assert fp.tell() == 0

    def test_chunks(self, storage):
        chunk_size = 32 * 1024
        chunk_counter = 0
        chunk_count = math.ceil(self.resource_size / chunk_size)
        with storage.resource.open():
            assert storage.resource.multiple_chunks(chunk_size) is True
            for chunk in storage.resource.chunks(chunk_size):
                chunk_counter += 1
            assert chunk_counter == chunk_count

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        pattern = posixpath.join(self.resource_url, 'Nature_Tree{suffix}.Jpeg')
        assert file_url == utils.get_target_filepath(pattern, file_url)

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_path(self, storage):
        path = storage.resource.path
        pattern = posixpath.join('media', self.resource_location, 'Nature_Tree{suffix}.Jpeg')
        assert path.endswith(utils.get_target_filepath(pattern, path))

    def test_url(self, storage):
        url = storage.resource.url
        pattern = posixpath.join(self.resource_url, 'Nature_Tree{suffix}.Jpeg')
        assert url == utils.get_target_filepath(pattern, url)


class TestFileFieldResourceAttach:
    resource_class = DummyFileFieldResource
    resource_size = 9711423
    resource_checksum = '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

    @contextmanager
    def get_resource(self):
        resource = self.resource_class()
        try:
            yield resource
        finally:
            resource.delete_file()

    def test_file(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                resource.attach_file(fp)

            assert resource.basename == 'milky-way-nasa'
            assert resource.extension == 'jpg'
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_django_file(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                file = File(fp, name='milky-way-nasa.jpg')
                resource.attach_file(file)

            assert resource.basename == 'milky-way-nasa'
            assert resource.extension == 'jpg'
            assert resource.size == self.resource_size
            assert resource.checksum == self.resource_checksum

    def test_override_name(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                resource.attach_file(fp, name='overwritten.jpg')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'jpg'

    def test_override_django_name(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                file = File(fp, name='not_used.png')
                resource.attach_file(file, name='overwritten.jpg')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'jpg'

    def test_wrong_extension(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                resource.attach_file(fp, name='overwritten.gif')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'gif'

    def test_file_position_at_end(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                resource.attach_file(fp)
                assert fp.tell() == self.resource_size


class TestFileFieldResourceRename:
    resource_class = DummyFileFieldResource
    resource_location = 'file_field'

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.rename_file('new_name.png')

        yield

        os.remove(storage.old_source_path)
        storage.resource.delete_file()
        storage.resource.delete()

    def test_old_file_exists(self, storage):
        assert os.path.exists(storage.old_source_path) is True

    def test_new_file_exists(self, storage):
        assert os.path.exists(storage.resource.get_file().path) is True

    def test_old_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.jpg'),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        file = storage.resource.get_file()
        assert file.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_name{suffix}.png'),
            file.name
        )

    def test_basename(self, storage):
        assert storage.resource.basename == utils.get_target_filepath(
            'new_name{suffix}',
            storage.resource.basename
        )

    def test_extension(self, storage):
        assert storage.resource.extension == 'png'


class TestFileFieldResourceDelete:
    resource_class = DummyFileFieldResource
    resource_location = 'file_field'

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp, name='old_name.jpg')
        storage.resource.save()

        file = storage.resource.get_file()
        storage.old_source_name = file.name
        storage.old_source_path = file.path
        storage.resource.delete_file()

        yield

        storage.resource.delete()

    def test_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.jpg'),
            storage.old_source_name
        )

    def test_file_not_exists(self, storage):
        assert os.path.exists(storage.old_source_path) is False


class TestFileFieldResourceEmpty:
    recource_class = DummyFileFieldResource

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.recource_class()
        yield

    def test_name(self, storage):
        with pytest.raises(ValueError):
            storage.resource.name

    def test_closed(self, storage):
        assert storage.resource.closed is True

    def test_open(self, storage):
        with pytest.raises(ValueError):
            storage.resource.open()  # noqa

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
        storage.resource.delete_file()


class TestImageFieldResource(TestFileFieldResource):
    resource_url = '/media/image_field'
    resource_location = 'image_field'
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = 'app'
    owner_model_name = 'dummyversatileimageresource'
    owner_fieldname = 'file'
    owner_class = DummyVersatileImageResource
    file_field_name = 'image'

    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyImageFieldResource(
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

    def test_title(self, storage):
        assert storage.resource.title == 'Calliphora'

    def test_description(self, storage):
        assert storage.resource.description == 'Calliphora is a genus of blow flies, ' \
                                               'also known as bottle flies'

    def test_name(self, storage):
        file_name = storage.resource.name
        pattern = posixpath.join(self.resource_location, 'Nature_Tree{suffix}.jpg')
        assert file_name == utils.get_target_filepath(pattern, file_name)

    def test_prepare_file(self, storage):
        obj = DummyImageFieldResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp)
            assert obj._prepare_file(file) is file
            assert obj.width == 3501
            assert obj.height == 2525

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
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
        }

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        pattern = posixpath.join(self.resource_url, 'Nature_Tree{suffix}.jpg')
        assert file_url == utils.get_target_filepath(pattern, file_url)

    def test_path(self, storage):
        path = storage.resource.path
        pattern = posixpath.join('media', self.resource_location, 'Nature_Tree{suffix}.jpg')
        assert path.endswith(utils.get_target_filepath(pattern, path))

    def test_url(self, storage):
        url = storage.resource.url
        pattern = posixpath.join(self.resource_url, 'Nature_Tree{suffix}.jpg')
        assert url == utils.get_target_filepath(pattern, url)


class TestImageFieldResourceAttach(TestFileFieldResourceAttach):
    resource_class = DummyImageFieldResource

    def test_wrong_extension(self):
        with self.get_resource() as resource:
            with open(NASA_FILEPATH, 'rb') as fp:
                resource.attach_file(fp, name='overwritten.gif')

            assert resource.basename == 'overwritten'
            assert resource.extension == 'jpg'  # extension detected by content


class TestImageFieldResourceRename(TestFileFieldResourceRename):
    resource_class = DummyImageFieldResource
    resource_location = 'image_field'


class TestImageFieldResourceDelete(TestFileFieldResourceDelete):
    resource_class = DummyImageFieldResource
    resource_location = 'image_field'


class TestImageFieldResourceEmpty(TestFileFieldResourceEmpty):
    recource_class = DummyFileFieldResource


class TestVersatileImageResource(TestImageFieldResource):
    resource_url = '/media/versatile_image'
    resource_location = 'versatile_image'
    resource_name = 'Nature Tree'
    resource_extension = 'jpg'
    resource_size = 672759
    resource_checksum = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
    owner_app_label = 'app'
    owner_model_name = 'dummyversatileimageresource'
    owner_fieldname = 'file'
    owner_class = DummyVersatileImageResource
    file_field_name = 'file'

    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyVersatileImageResource(
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
            'url': storage.resource.get_file_url(),
            'created': storage.resource.created_at.isoformat(),
            'modified': storage.resource.modified_at.isoformat(),
            'uploaded': storage.resource.uploaded_at.isoformat(),
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


class TestImageAttach(TestImageFieldResourceAttach):
    resource_class = DummyVersatileImageResource


class TestImageRename(TestImageFieldResourceRename):
    resource_class = DummyVersatileImageResource
    resource_location = 'versatile_image'

    @classmethod
    def init_class(cls, storage):
        storage.resource = DummyVersatileImageResource()
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

    def test_old_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.jpg'),
            storage.old_source_name
        )
        assert storage.old_desktop_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.desktop.jpg'),
            storage.old_source_name
        )
        assert storage.old_mobile_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.mobile.jpg'),
            storage.old_source_name
        )

    def test_new_file_name(self, storage):
        assert storage.resource.file.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_name{suffix}.png'),
            storage.resource.file.name
        )
        assert storage.resource.desktop.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_name{suffix}.desktop.png'),
            storage.resource.file.name
        )
        assert storage.resource.mobile.name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'new_name{suffix}.mobile.png'),
            storage.resource.file.name
        )

    def test_old_file_exists(self, storage):
        assert os.path.exists(storage.old_source_path) is True
        assert os.path.exists(storage.old_desktop_path) is True
        assert os.path.exists(storage.old_mobile_path) is True

    def test_new_file_exists(self, storage):
        assert os.path.exists(storage.resource.get_file().path) is True
        assert os.path.exists(storage.resource.desktop.path) is True
        assert os.path.exists(storage.resource.mobile.path) is True


class TestImageDelete(TestImageFieldResourceDelete):
    resource_class = DummyVersatileImageResource
    resource_location = 'versatile_image'

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
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

    def test_file_name(self, storage):
        assert storage.old_source_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.jpg'),
            storage.old_source_name
        )
        assert storage.old_desktop_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.desktop.jpg'),
            storage.old_source_name
        )
        assert storage.old_mobile_name == utils.get_target_filepath(
            posixpath.join(self.resource_location, 'old_name{suffix}.mobile.jpg'),
            storage.old_source_name
        )

    def test_file_not_exists(self, storage):
        assert os.path.exists(storage.old_source_path) is False
        assert os.path.exists(storage.old_desktop_path) is False
        assert os.path.exists(storage.old_mobile_path) is False


class TestImageEmpty(TestImageFieldResourceEmpty):
    recource_class = DummyVersatileImageResource

    def test_variation_files(self, storage):
        assert list(storage.resource.variation_files()) == []

    def test_variation_attribute(self, storage):
        with pytest.raises(AttributeError):
            storage.resource.desktop  # noqa


@pytest.mark.django_db
class TestImageResourceVariations:
    resource_class = DummyVersatileImageResource

    def test_variation_attributes_after_delete(self):
        resource = self.resource_class()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.delete_file()

        with pytest.raises(AttributeError):
            resource.desktop  # noqa

    def test_variation_files_after_delete(self):
        resource = self.resource_class()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.delete_file()

        assert list(resource.variation_files()) == []

    def test_reattach_file(self):
        resource = self.resource_class()
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
        resource = self.resource_class()
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

    def test_recut(self):
        resource = self.resource_class()
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

    def test_variation_created_signal(self):
        resource = self.resource_class()
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
