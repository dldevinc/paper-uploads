import re
import os
import pytest
from pathlib import Path
from django.core.files import File
from django.utils.timezone import now
from django.template.defaultfilters import filesizeformat
from tests.app.models import Page
from .. import validators
from ..models import UploadedFile, FileField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestUploadedFile:
    def test_file(self):
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            obj = UploadedFile(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='file'
            )
            obj.attach_file(File(fp, name='Doc.PDF'))
            obj.save()

        try:
            suffix = re.match(r'Doc((?:_\w+)?)', os.path.basename(obj.file.name)).group(1)

            assert obj.PROXY_FILE_ATTRIBUTES == {'url', 'path', 'open', 'read', 'close', 'closed'}
            assert obj.name == 'Doc'
            assert obj.display_name == 'Doc'
            assert obj.canonical_name == 'Doc.pdf'
            assert obj.extension == 'pdf'
            assert obj.size == 9678
            assert obj.hash == 'bebc2ddd2a8b8270b359990580ff346d14c021fa'

            assert os.path.isfile(obj.path)
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
            assert obj.get_owner_field() is Page._meta.get_field('file')
            assert obj.get_validation() == {}

            # FileFieldContainerMixin methods
            assert obj.get_file_name() == 'files/{}/Doc{}.pdf'.format(now().strftime('%Y-%m-%d'), suffix)
            assert obj.get_file_size() == 9678
            assert obj.file_exists() is True
            assert obj.get_file_hash() == 'bebc2ddd2a8b8270b359990580ff346d14c021fa'
            assert obj.get_file_url() == '/media/files/{}/Doc{}.pdf'.format(now().strftime('%Y-%m-%d'), suffix)
        finally:
            obj.delete()

        assert obj.file_exists() is False

    def test_orphan_file(self):
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as fp:
            obj = UploadedFile()
            obj.attach_file(File(fp, name='Doc.PDF'))
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete()

        assert obj.file_exists() is False


class TestFileField:
    def test_rel(self):
        field = FileField()
        assert field.null is True
        assert field.related_model == 'paper_uploads.UploadedFile'
        assert field.postprocess is None

    def test_validators(self):
        field = FileField(validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
            validators.MimetypeValidator(['image/jpeg', 'image/bmp', 'image/Png'])
        ])
        field.contribute_to_class(Page, 'file')

        assert field.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png')
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ('image/jpeg', 'image/bmp', 'image/png')
        }
