import os
import re
import shutil

import pytest
from django.conf import settings
from django.core.files import File
from django.utils.timezone import now

from app.models import (
    DummyFileFieldResource,
    DummyFileResource,
    DummyImageFieldResource,
    DummyReadonlyFileProxyResource,
    DummyResource,
    DummyVersatileImageResource,
    VariationFile,
)
from paper_uploads import signals
from paper_uploads.variations import PaperVariation

from ..dummy import *


@pytest.fixture(scope='class')
def resource(class_scoped_db):
    resource = DummyResource.objects.create(
        name='Milky Way'
    )
    yield resource
    resource.delete()


@pytest.fixture(scope='class')
def file_resource(class_scoped_db):
    resource = DummyFileResource.objects.create(
        name='Dummy File',
        extension='pdf',
        size=12345
    )
    yield resource
    resource.delete()


@pytest.fixture(scope='class')
def file_field_resource(class_scoped_db):
    resource = DummyFileFieldResource()
    with open(NATURE_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()
    yield resource
    resource.delete_file()
    resource.delete()


@pytest.fixture(scope='class')
def image_resource(class_scoped_db):
    resource = DummyImageFieldResource(
        title='Calliphora',
        description='Calliphora is a genus of blow flies, also known as bottle flies'
    )
    with open(CALLIPHORA_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()
    yield resource
    resource.delete_file()
    resource.delete()


@pytest.fixture(scope='class')
def variation_file(class_scoped_db):
    resource = DummyImageFieldResource()
    with open(NASA_FILEPATH, 'rb') as fp:
        resource.attach_file(fp)
    resource.save()

    yield VariationFile(resource, 'desktop')

    resource.delete_file()
    resource.delete()


@pytest.mark.django_db
class TestResource:
    def _equal_dates(self, date1, date2):
        return abs((date2 - date1).seconds) < 5

    def test_name(self, resource):
        assert resource.name == 'Milky Way'

    def test_dates(self, resource):
        assert self._equal_dates(resource.created_at, now())
        assert self._equal_dates(resource.modified_at, now())
        assert self._equal_dates(resource.uploaded_at, now())

    def test_str(self, resource):
        assert str(resource) == 'Milky Way'

    def test_repr(self, resource):
        assert repr(resource) == "DummyResource('Milky Way')"

    def test_as_dict(self, resource):
        assert resource.as_dict() == {
            'id': 1,
            'name': 'Milky Way'
        }

    def test_get_owner_model(self):
        resource = DummyResource(
            owner_app_label='app',
            owner_model_name='dummyfilefieldresource',
            owner_fieldname='file'
        )
        assert resource.get_owner_model() is DummyFileFieldResource

    def test_missing_owner_model(self):
        resource = DummyResource(
            owner_app_label='app',
            owner_model_name='noexistent',
            owner_fieldname='file'
        )
        assert resource.get_owner_model() is None

    def test_get_owner_field(self):
        resource = DummyResource(
            owner_app_label='app',
            owner_model_name='dummyfilefieldresource',
            owner_fieldname='file'
        )
        assert resource.get_owner_field() is DummyFileFieldResource._meta.get_field('file')

    def test_missing_owner_field(self):
        resource = DummyResource(
            owner_app_label='app',
            owner_model_name='noexistent',
            owner_fieldname='file'
        )
        assert resource.get_owner_field() is None


@pytest.mark.django_db
class TestFileResource:
    def test_get_hash(self, file_resource):
        with open(NASA_FILEPATH, 'rb') as fp:
            content_hash = file_resource.get_hash(fp)
        assert content_hash == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

    def test_django_file_get_hash(self, file_resource):
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp)
            content_hash = file_resource.get_hash(file)
        assert content_hash == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

    def test_update_hash(self, file_resource):
        file_resource.content_hash = ''

        with open(NASA_FILEPATH, 'rb') as fp:
            assert file_resource.update_hash(fp) is True
            assert file_resource.content_hash == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

        with open(NASA_FILEPATH, 'rb') as fp:
            assert file_resource.update_hash(fp) is False
            assert file_resource.content_hash == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

    def test_update_hash_signal(self, file_resource):
        signal_fired = False
        file_resource.content_hash = ''

        def signal_handler(sender, instance, content_hash, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is file_resource
            assert content_hash == '485291fa0ee50c016982abbfa943957bcd231aae0492ccbaa22c58e3997b35e0'

        signals.content_hash_update.connect(signal_handler)

        with open(NASA_FILEPATH, 'rb') as fp:
            assert signal_fired is False
            assert file_resource.update_hash(fp) is True
            assert signal_fired is True

    def test_str(self, file_resource):
        assert str(file_resource) == 'Dummy File.pdf'

    def test_repr(self, file_resource):
        assert repr(file_resource) == "DummyFileResource('Dummy File.pdf')"

    def test_get_basename(self, file_resource):
        assert file_resource.get_basename() == 'Dummy File.pdf'

    def test_get_file_name(self, file_resource):
        assert file_resource.get_file_name() == 'File_ABCD.jpg'

    def test_get_file_url(self, file_resource):
        assert file_resource.get_file_url() == 'http://example.com/Dummy%20File.pdf'

    def test_as_dict(self, file_resource):
        assert file_resource.as_dict() == {
            'id': 1,
            'name': 'Dummy File',
            'extension': 'pdf',
            'size': 12345,
            'url': 'http://example.com/Dummy%20File.pdf'
        }

    def test_file_exists(self, file_resource):
        assert file_resource.file_exists() is True

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
        assert resource.extension == 'jpg'  # extension from get_file_name()
        assert resource.get_basename() == 'overwritten.jpg'

        resource.delete_file()

    def test_named_django_file_attach_file(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp, name='overwritten.png')
            resource.attach_file(file)

        assert resource.name == 'overwritten'
        assert resource.extension == 'jpg'  # extension from get_file_name()
        assert resource.get_basename() == 'overwritten.jpg'

        resource.delete_file()

    def test_override_django_file_name_attach_file(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            file = File(fp, name='new name.png')
            resource.attach_file(file, name='override.gif')

        assert resource.name == 'override'
        assert resource.extension == 'jpg'  # extension from get_file_name()
        assert resource.get_basename() == 'override.jpg'

        resource.delete_file()

    def test_attach_file_reset_file_position(self):
        resource = DummyFileResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
            assert fp.tell() == 0

        resource.delete_file()

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
            assert instance.extension == ''
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

    def test_pre_rename_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, new_name, options, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource
            assert instance.name == 'milky-way-nasa'
            assert instance.extension == 'jpg'
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

    def test_post_rename_file_signal(self):
        resource = DummyFileResource()
        signal_fired = False

        def signal_handler(sender, instance, new_name, options, response, **kwargs):
            nonlocal signal_fired
            signal_fired = True
            assert sender is DummyFileResource
            assert instance is resource
            assert instance.name == 'new name'
            assert instance.extension == 'png'
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


@pytest.mark.django_db
class TestFileFieldResource:
    def test_name(self, file_field_resource):
        assert file_field_resource.name == 'nature'

    def test_extension(self, file_field_resource):
        assert file_field_resource.extension == 'jpeg'

    def test_size(self, file_field_resource):
        assert file_field_resource.size == 672759

    def test_content_hash(self, file_field_resource):
        assert file_field_resource.content_hash == 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'

    def test_file_exists(self, file_field_resource):
        assert file_field_resource.file_exists() is True

    def test_get_basename(self, file_field_resource):
        assert file_field_resource.get_basename() == 'nature.jpeg'

    def test_get_file_name(self, file_field_resource):
        file_name = file_field_resource.get_file_name()
        match = re.match(r'file_field/nature(_\w+)?\.jpeg', file_name)
        assert match is not None

    def test_get_file_url(self, file_field_resource):
        file_url = file_field_resource.get_file_url()
        match = re.match(r'/media/file_field/nature(_\w+)?\.jpeg', file_url)
        assert match is not None

    def test_as_dict(self, file_field_resource):
        file_url = file_field_resource.get_file_url()
        match = re.match(r'/media/file_field/nature(_\w+)?\.jpeg', file_url)
        suffix = match.group(1) or ''
        assert file_field_resource.as_dict() == {
            'id': 1,
            'name': 'nature',
            'extension': 'jpeg',
            'size': 672759,
            'url': '/media/file_field/nature{}.jpeg'.format(suffix)
        }

    def test_rename_file(self):
        resource = DummyFileFieldResource()
        with open(NASA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='old_name.jpg')
        resource.save()

        old_source_path = resource.file.path
        assert os.path.exists(old_source_path) is True

        resource.rename_file('new_name.png')

        # ensure old file still exists
        assert os.path.exists(old_source_path) is True
        assert os.path.exists(resource.file.path) is True

        assert resource.get_file_name() == 'file_field/new_name.png'

        os.remove(old_source_path)
        resource.delete_file()
        resource.delete()

    def test_delete_file(self):
        resource = DummyFileFieldResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        source_path = resource.file.path
        assert os.path.exists(source_path) is True

        resource.delete_file()
        assert os.path.exists(source_path) is False

        resource.delete()


@pytest.mark.django_db
class TestEmptyFileFieldResource:
    def test_name(self):
        resource = DummyFileFieldResource()
        with pytest.raises(FileNotFoundError):
            resource.get_file_name()

    def test_url(self):
        resource = DummyFileFieldResource()
        with pytest.raises(FileNotFoundError):
            resource.get_file_url()

    def test_file_exists(self):
        resource = DummyFileFieldResource()
        assert resource.file_exists() is False

    def test_rename_file(self):
        resource = DummyFileFieldResource()
        with pytest.raises(FileNotFoundError):
            resource.rename_file('bla-bla.jpg')

    def test_delete_file(self):
        resource = DummyFileFieldResource()
        resource.delete_file()


@pytest.mark.django_db
class TestImageFieldResource:
    def test_title(self, image_resource):
        assert image_resource.title == 'Calliphora'

    def test_description(self, image_resource):
        assert image_resource.description == 'Calliphora is a genus of blow flies, ' \
                                             'also known as bottle flies'

    def test_width(self, image_resource):
        assert image_resource.width == 804

    def test_height(self, image_resource):
        assert image_resource.height == 1198

    def test_as_dict(self, image_resource):
        file_url = image_resource.get_file_url()
        match = re.match(r'/media/image_field/calliphora(_\w+)?\.jpg', file_url)
        suffix = match.group(1) or ''
        assert image_resource.as_dict() == {
            'id': 1,
            'name': 'calliphora',
            'extension': 'jpg',
            'size': 254766,
            'url': '/media/image_field/calliphora{}.jpg'.format(suffix),
            'width': 804,
            'height': 1198,
            'title': 'Calliphora',
            'description': 'Calliphora is a genus of blow flies, also known as bottle flies',
            'cropregion': ''
        }


class TestVariationFile:
    def test_instance(self, variation_file):
        assert isinstance(variation_file.instance, DummyImageFieldResource)

    def test_variation_name(self, variation_file):
        assert variation_file.variation_name == 'desktop'

    def test_name(self, variation_file):
        file_name = variation_file.instance.get_file_name()
        match = re.match(r'image_field/milky-way-nasa(_\w+)?\.jpg', file_name)
        suffix = match.group(1) or ''
        assert variation_file.name == 'image_field/milky-way-nasa{}.desktop.jpg'.format(suffix)

    def test_variation(self, variation_file):
        assert isinstance(variation_file.variation, PaperVariation)

    def test_path(self, variation_file):
        file_name = variation_file.instance.get_file_name()
        match = re.match(r'image_field/milky-way-nasa(_\w+)?\.jpg', file_name)
        suffix = match.group(1) or ''
        assert (
            variation_file.path ==
            os.path.join(
                settings.BASE_DIR,
                'media/image_field/milky-way-nasa{}.desktop.jpg'.format(suffix)
            )
        )

    def test_url(self, variation_file):
        file_name = variation_file.instance.get_file_name()
        match = re.match(r'image_field/milky-way-nasa(_\w+)?\.jpg', file_name)
        suffix = match.group(1) or ''
        assert variation_file.url == '/media/image_field/milky-way-nasa{}.desktop.jpg'.format(suffix)

    def test_size(self, variation_file):
        assert variation_file.size == 478196

    def test_exists(self, variation_file):
        assert variation_file.exists() is True

    def test_width(self, variation_file):
        assert variation_file.width == 800

    def test_height(self, variation_file):
        assert variation_file.height == 577

    def test_open(self, variation_file):
        assert variation_file.closed is True
        with variation_file.open():
            assert variation_file.closed is False
        assert variation_file.closed is True

    def test_delete(self, variation_file):
        source_name = variation_file.name
        source_file = variation_file.path
        backup_file = os.path.join(settings.BASE_DIR, 'media/image_field/nasa.bak.jpg')
        shutil.copyfile(source_file, backup_file)

        variation_file.delete()
        assert variation_file.exists() is False

        with pytest.raises(ValueError):
            x = variation_file.path

        with pytest.raises(ValueError):
            x = variation_file.url

        with pytest.raises(ValueError):
            x = variation_file.size

        with pytest.raises(ValueError):
            variation_file.open()

        assert variation_file.exists() is False

        variation_file.name = source_name
        shutil.move(backup_file, source_file)

    def test_delete_unexisted(self, variation_file):
        source_name = variation_file.name
        source_file = variation_file.path
        backup_file = os.path.join(settings.BASE_DIR, 'media/image_field/nasa.bak.jpg')
        shutil.copyfile(source_file, backup_file)

        variation_file.delete()
        assert variation_file.exists() is False

        # call again
        variation_file.delete()

        variation_file.name = source_name
        shutil.move(backup_file, source_file)


@pytest.mark.django_db
class TestVersatileImageResource:
    def test_variation_attribute(self):
        resource = DummyVersatileImageResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        assert isinstance(resource.desktop, VariationFile)
        assert isinstance(resource.mobile, VariationFile)
        assert resource.desktop.exists() is True
        assert resource.mobile.exists() is True
        with pytest.raises(AttributeError):
            resource.tablet  # noqa

        resource.delete_file()
        
        with pytest.raises(AttributeError):
            resource.desktop  # noqa
        
        resource.delete()

    def test_variation_files(self):
        resource = DummyVersatileImageResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='test_files.jpg')

        assert dict(resource.variation_files()) == {
            'desktop': resource.desktop,
            'mobile': resource.mobile,
        }

        resource.delete_file()

        assert list(resource.variation_files()) == []

    def test_reattach_file(self):
        resource = DummyVersatileImageResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='initial_image.jpg')

        assert resource.desktop.name == 'versatile_image/initial_image.desktop.jpg'
        assert resource._variation_files_cache == {
            'desktop': resource.desktop,
            'mobile': resource.mobile,
        }

        os.remove(resource.file.path)
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp, name='new_image.jpg')

        assert resource.desktop.name == 'versatile_image/new_image.desktop.jpg'
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

    def test_calculate_max_size(self):
        resource = DummyVersatileImageResource()
        assert resource.calculate_max_size((3000, 2000)) == (900, 600)
        assert resource.calculate_max_size((2000, 3000)) == (800, 1200)

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


@pytest.mark.django_db
class TestEmptyVersatileImageResource:
    def test_name(self):
        resource = DummyVersatileImageResource()
        with pytest.raises(FileNotFoundError):
            resource.get_file_name()

    def test_url(self):
        resource = DummyVersatileImageResource()
        with pytest.raises(FileNotFoundError):
            resource.get_file_url()

    def test_file_exists(self):
        resource = DummyVersatileImageResource()
        assert resource.file_exists() is False

    def test_rename_file(self):
        resource = DummyVersatileImageResource()
        with pytest.raises(FileNotFoundError):
            resource.rename_file('bla-bla.jpg')

    def test_delete_file(self):
        resource = DummyVersatileImageResource()
        resource.delete_file()

    def test_variation_files(self):
        resource = DummyVersatileImageResource()
        assert list(resource.variation_files()) == []

    def test_variation_attribute(self):
        resource = DummyVersatileImageResource()
        with pytest.raises(AttributeError):
            resource.desktop  # noqa


@pytest.mark.django_db
class TestReadonlyFileProxyResource:
    def test_open(self):
        resource = DummyReadonlyFileProxyResource()
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)

        with resource as fp:
            assert fp.read(4) == b'\xff\xd8\xff\xe0'

        resource.delete_file()

    def test_closed(self):
        resource = DummyReadonlyFileProxyResource()
        with open(NATURE_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        resource.file.close()  # close file explicitly

        assert resource.closed is True
        with resource.open():
            assert resource.closed is False
        assert resource.closed is True

        resource.delete_file()
        resource.delete()

    def test_properties(self):
        resource = DummyReadonlyFileProxyResource()
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            resource.attach_file(fp)
        resource.save()

        assert resource.path.endswith('/media/readonly_file/calliphora.jpg')
        assert resource.url == '/media/readonly_file/calliphora.jpg'

        assert resource.tell() == 254766
        resource.seek(0)
        assert resource.tell() == 0
        assert resource.read(4) == b'\xff\xd8\xff\xe0'

        resource.delete_file()
        resource.delete()
