import re
import pytest
from pathlib import Path
from django.core.files import File
from tests.app.models import Page
from ..models import CloudinaryMedia

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryMedia:
    def test_media(self):
        with open(TESTS_PATH / 'audio.ogg', 'rb') as fp:
            object = CloudinaryMedia(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_video'
            )
            object.attach_file(File(fp, name='audio.ogg'))
            object.save()

        try:
            assert object.PROXY_FILE_ATTRIBUTES == {'url'}
            assert object.cloudinary_resource_type == 'video'
            assert object.cloudinary_type == 'upload'
            assert object.file.resource_type == 'video'
            assert object.file.type == 'upload'

            assert object.name == 'audio'
            assert object.display_name == 'audio'
            assert object.canonical_name == 'audio.ogg'
            assert object.extension == 'ogg'
            assert object.size == 105243
            assert object.hash == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'

            # SlaveModelMixin methods
            assert object.get_owner_model() is Page
            assert object.get_owner_field() is Page._meta.get_field('cloud_video')
            assert object.get_validation() == {
                'acceptFiles': ['.3gp', '.avi', '.flv', '.mkv', '.mov', '.wmv', '.aac', '.wma', 'video/*', 'audio/*']
            }

            # CloudinaryContainerMixin methods
            assert re.fullmatch(r'\w+', object.get_public_id()) is not None
            assert re.fullmatch(r'\w+\.ogg', object.get_file_name()) is not None
            assert object.get_file_size() == 105243
            assert object.file_exists() is True
            assert object.get_file_hash() == '4fccac8855634c2dccbd806aa7fc4ac3879e5a35'
            assert re.fullmatch(r'http://res.cloudinary.com/[^/]+/video/upload/[^/]+/audio_\w+.ogg', object.get_file_url()) is not None

            for name in object.PROXY_FILE_ATTRIBUTES:
                assert getattr(object, name) == getattr(object.file, name)
        finally:
            object.delete()

        assert object.file_exists() is False

    def test_orphan_media(self):
        with open(TESTS_PATH / 'audio.ogg', 'rb') as fp:
            object = CloudinaryMedia()
            object.attach_file(File(fp, name='audio.ogg'))
            object.save()

        try:
            assert object.get_owner_model() is None
            assert object.get_owner_field() is None
        finally:
            object.delete()

        assert object.file_exists() is False
