import re
from pathlib import Path
from datetime import timedelta

import cloudinary.uploader
import pytest
from django.template.defaultfilters import filesizeformat
from django.utils.timezone import now
from tests.app.models import Page

from ... import validators
from ..models import CloudinaryMedia, CloudinaryMediaField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryMedia:
    def test_file(self):
        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as svg_file:
            obj = CloudinaryMedia(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file',
            )
            obj.attach_file(svg_file, name='audio.OGG')
            obj.save()

        try:
            # Resource
            assert obj.name == 'audio'
            assert now() - obj.created_at < timedelta(seconds=10)
            assert now() - obj.uploaded_at < timedelta(seconds=10)
            assert now() - obj.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert obj.hash == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'

            # FileResource
            assert obj.extension == 'ogg'
            assert obj.size == 105243
            assert str(obj) == 'audio.ogg'
            assert repr(obj) == "CloudinaryMedia('audio.ogg')"
            assert obj.get_basename() == 'audio.ogg'
            assert obj.get_file() is obj.file
            assert re.fullmatch(r'audio\w+\.ogg', obj.get_file_name()) is not None
            assert (
                re.fullmatch(
                    r'http://res\.cloudinary\.com/[^/]+/video/upload/[^/]+/audio_\w+\.ogg',
                    obj.get_file_url(),
                )
                is not None
            )
            assert obj.is_file_exists() is True

            # ReverseFieldModelMixin
            assert obj.owner_app_label == 'app'
            assert obj.owner_model_name == 'page'
            assert obj.owner_fieldname == 'cloud_file'
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('cloud_file')

            # ReadonlyFileProxyMixin
            assert obj.url == obj.get_file_url()

            with pytest.raises(AttributeError):
                print(obj.path)

            assert obj.closed is True
            with obj.open():
                assert obj.closed is False
                assert obj.read(4) == b'OggS'
                assert obj.tell() == 4
                obj.seek(0)
                assert obj.tell() == 0
                assert obj.closed is False
            assert obj.closed is True

            # CloudinaryFileResource
            assert obj.cloudinary_resource_type == 'video'
            assert obj.cloudinary_type == 'upload'

            cloudinary_field = obj._meta.get_field('file')
            assert cloudinary_field.type == obj.cloudinary_type
            assert cloudinary_field.resource_type == obj.cloudinary_resource_type

            obj.refresh_from_db()
            assert re.fullmatch(r'audio\w+', obj.get_public_id()) is not None

            # CloudinaryMedia
            assert obj.display_name == 'audio'

            assert obj.get_validation() == {
                'acceptFiles': [
                    '.3gp',
                    '.avi',
                    '.flv',
                    '.mkv',
                    '.mov',
                    '.wmv',
                    '.aac',
                    '.wma',
                    'video/*',
                    'audio/*',
                ],
            }

            # as_dict
            assert obj.as_dict() == {
                'id': obj.pk,
                'name': obj.name,
                'extension': obj.extension,
                'size': obj.size,
                'url': obj.get_file_url(),
                'file_info': '({ext}, {size})'.format(
                    ext=obj.extension, size=filesizeformat(obj.size)
                ),
            }
        finally:
            obj.delete_file()
            assert obj.is_file_exists() is False

            obj.delete()

    def test_orphan_file(self):
        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as pdf_file:
            obj = CloudinaryMedia()
            obj.attach_file(pdf_file)
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete_file()
            obj.delete()

    def test_empty_file(self):
        obj = CloudinaryMedia(
            owner_app_label="app",
            owner_model_name="page",
            owner_fieldname="cloud_file",
        )
        try:
            assert obj.closed is True
            assert bool(obj.file) is False
            with pytest.raises(AttributeError):
                obj.get_file_url()
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()

    def test_missing_file(self):
        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as pdf_file:
            obj = CloudinaryMedia(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file',
            )
            obj.attach_file(pdf_file)
            obj.save()

        cloudinary.uploader.destroy(
            obj.get_public_id(),
            type=obj.cloudinary_type,
            resource_type=obj.cloudinary_resource_type,
        )

        try:
            assert obj.closed is True
            assert re.fullmatch(r'audio\w+\.ogg', obj.get_file_name()) is not None
            assert (
                re.fullmatch(
                    r'http://res\.cloudinary\.com/[^/]+/video/upload/[^/]+/audio\w+\.ogg',
                    obj.get_file_url(),
                )
                is not None
            )
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()
            obj.delete()

    def test_file_rename(self):
        with open(str(TESTS_PATH / 'audio.ogg'), 'rb') as audio_file:
            obj = CloudinaryMedia(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_media',
            )
            obj.attach_file(audio_file)
            obj.save()

        old_public_id = obj.get_public_id()

        try:
            # check old file
            assert isinstance(
                cloudinary.uploader.explicit(
                    old_public_id,
                    type=obj.cloudinary_type,
                    resource_type=obj.cloudinary_resource_type,
                ),
                dict,
            )
            assert obj.is_file_exists()

            obj.rename_file('new_name')

            # TODO: старый файл не сохраняется
            # # recheck old file
            # assert isinstance(cloudinary.uploader.explicit(
            #     old_public_id,
            #     type=obj.cloudinary_type,
            #     resource_type=obj.cloudinary_resource_type
            # ), dict)

            # check new file
            new_public_id = obj.get_public_id()
            assert obj.name == 'new_name'
            assert re.search(r'new_name_\w+\.ogg$', obj.get_file_name()) is not None
            assert obj.is_file_exists()
            assert isinstance(
                cloudinary.uploader.explicit(
                    new_public_id,
                    type=obj.cloudinary_type,
                    resource_type=obj.cloudinary_resource_type,
                ),
                dict,
            )
        finally:
            cloudinary.uploader.destroy(
                old_public_id,
                type=obj.cloudinary_type,
                resource_type=obj.cloudinary_resource_type,
            )

            obj.delete_file()
            obj.delete()


class TestCloudinaryMediaField:
    def test_rel(self):
        field = CloudinaryMediaField()
        assert field.null is True
        assert field.related_model == 'paper_uploads_cloudinary.CloudinaryMedia'

    def test_validators(self):
        field = CloudinaryMediaField(
            validators=[
                validators.SizeValidator(10 * 1024 * 1024),
                validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
                validators.MimetypeValidator(['image/jpeg', 'image/bmp', 'image/Png']),
            ]
        )
        field.contribute_to_class(Page, 'cloud_file')

        assert field.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png'),
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png'),
        }

    def test_cloudinary_options(self):
        field = CloudinaryMediaField(cloudinary={
            'public_id': 'myimage',
            'folder': 'media',
        })
        assert field.cloudinary_options == {
            'public_id': 'myimage',
            'folder': 'media',
        }
