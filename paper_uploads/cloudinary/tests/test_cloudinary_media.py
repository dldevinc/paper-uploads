import re
import pytest
from pathlib import Path
from django.core.files import File
from django.template.defaultfilters import filesizeformat
from tests.app.models import Page
from ... import validators
from ..models import CloudinaryMedia, CloudinaryMediaField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryMedia:
    def test_media(self):
        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            obj = CloudinaryMedia(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_video'
            )
            obj.attach_file(File(audio_file, name='audio.ogg'))
            obj.save()

        try:
            assert obj.PROXY_FILE_ATTRIBUTES == {'url'}
            assert obj.cloudinary_resource_type == 'video'
            assert obj.cloudinary_type == 'upload'
            assert obj.file.resource_type == 'video'
            assert obj.file.type == 'upload'

            assert obj.name == 'audio'
            assert obj.display_name == 'audio'
            assert obj.canonical_name == 'audio.ogg'
            assert obj.extension == 'ogg'
            assert obj.size == 105243
            assert obj.hash == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'

            assert obj.as_dict() == {
                'id': obj.pk,
                'name': obj.display_name,
                'ext': obj.extension,
                'size': obj.size,
                'url': obj.get_file_url(),
                'file_info': '({ext}, {size})'.format(
                    ext=obj.extension,
                    size=filesizeformat(obj.size)
                )
            }

            for name in obj.PROXY_FILE_ATTRIBUTES:
                assert getattr(obj, name) == getattr(obj.file, name)

            # SlaveModelMixin methods
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('cloud_video')
            assert obj.get_validation() == {
                'acceptFiles': ['.3gp', '.avi', '.flv', '.mkv', '.mov', '.wmv', '.aac', '.wma', 'video/*', 'audio/*']
            }

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+', obj.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.ogg', obj.get_file_name()) is not None
            assert obj.get_file_size() == 105243
            assert obj.file_exists() is True
            assert obj.get_file_hash() == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/video/upload/[^/]+/audio_\w+\.ogg', obj.get_file_url()) is not None
        finally:
            obj.delete()

        assert obj.file_exists() is False

    def test_orphan_media(self):
        with open(TESTS_PATH / 'audio.ogg', 'rb') as audio_file:
            obj = CloudinaryMedia()
            obj.attach_file(File(audio_file, name='audio.ogg'))
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete()

        assert obj.file_exists() is False


class TestCloudinaryMediaField:
    def test_rel(self):
        field = CloudinaryMediaField()
        assert field.null is True
        assert field.related_model == 'paper_uploads_cloudinary.CloudinaryMedia'

    def test_validators(self):
        field = CloudinaryMediaField(validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
        ])
        field.contribute_to_class(Page, 'cloud_video')

        assert field.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ['.3gp', '.avi', '.flv', '.mkv', '.mov', '.wmv', '.aac', '.wma', 'video/*', 'audio/*']
        }

    def test_cloudinary_options(self):
        field = CloudinaryMediaField(public_id='mymedia', folder='media')
        assert field.cloudinary_options == {
            'use_filename': True,
            'unique_filename': True,
            'overwrite': True,
            'public_id': 'mymedia',
            'folder': 'media',
        }
