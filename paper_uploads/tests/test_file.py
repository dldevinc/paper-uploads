import os
import re
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.timezone import now
from tests.app.models import Page

from .. import validators
from ..models import FileField, UploadedFile

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestUploadedFile:
    def test_file(self):
        with open(str(TESTS_PATH / "cartman.svg"), "rb") as svg_file:
            obj = UploadedFile(
                owner_app_label="app",
                owner_model_name="page",
                owner_fieldname="file",
            )
            obj.attach_file(svg_file, name="Cartman.SVG")
            obj.save()

        suffix_match = re.match(r"Cartman((?:_\w+)?)", os.path.basename(obj.file.name))
        assert suffix_match is not None
        suffix = suffix_match.group(1)

        try:
            # Resource
            assert obj.name == 'Cartman'
            assert now() - obj.created_at < timedelta(seconds=10)
            assert now() - obj.uploaded_at < timedelta(seconds=10)
            assert now() - obj.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert obj.hash == '563bca379c51c21a7bdff080f7cff67914040c10'

            # FileResource
            assert obj.extension == 'svg'
            assert obj.size == 1118
            assert str(obj) == 'Cartman.svg'
            assert repr(obj) == "UploadedFile('Cartman.svg')"
            assert obj.get_basename() == 'Cartman.svg'
            assert obj.get_file() is obj.file
            assert (
                obj.get_file_name() == "files/{}/Cartman{}.svg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert (
                obj.get_file_url() == "/media/files/{}/Cartman{}.svg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert obj.is_file_exists() is True

            # FileFieldResource
            assert os.path.isfile(obj.path)

            # PostrocessableFileFieldResource
            assert os.stat(str(TESTS_PATH / 'cartman.svg')).st_size == 1183

            # ReverseFieldModelMixin
            assert obj.owner_app_label == 'app'
            assert obj.owner_model_name == 'page'
            assert obj.owner_fieldname == 'file'
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('file')

            # ReadonlyFileProxyMixin
            assert obj.url == obj.get_file_url()
            assert obj.path == os.path.join(
                settings.BASE_DIR, settings.MEDIA_ROOT, obj.get_file_name()
            )
            assert obj.closed is True
            with obj.open():
                assert obj.closed is False
                assert obj.read(4) == b'<svg'
                assert obj.tell() == 4
                obj.seek(0)
                assert obj.tell() == 0
                assert obj.closed is False
            assert obj.closed is True

            with obj.open('r'):
                assert obj.read(4) == '<svg'

            # UploadedFile
            assert obj.display_name == 'Cartman'

            # as_dict
            assert obj.as_dict() == {
                'id': obj.pk,
                'name': obj.name,
                'extension': obj.extension,
                'size': obj.size,
                'url': obj.get_file_url(),
                'file_info': '({ext}, {size})'.format(
                    ext=obj.extension,
                    size=filesizeformat(obj.size)
                ),
            }
        finally:
            file_path = obj.path
            assert os.path.isfile(file_path) is True
            obj.delete_file()
            assert os.path.isfile(file_path) is False
            assert obj.is_file_exists() is False

            obj.delete()

    def test_orphan_file(self):
        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            obj = UploadedFile()
            obj.attach_file(pdf_file, name='Doc.PDF')
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete_file()
            obj.delete()

    def test_empty_file(self):
        obj = UploadedFile(
            owner_app_label="app",
            owner_model_name="page",
            owner_fieldname="file",
        )
        try:
            assert obj.closed is True
            assert bool(obj.file) is False
            with pytest.raises(ValueError):
                obj.get_file_url()
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()

    def test_missing_file(self):
        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            obj = UploadedFile()
            obj.attach_file(pdf_file, name='Doc.PDF')
            obj.save()

        os.unlink(obj.path)
        suffix_match = re.match(r"Doc((?:_\w+)?)", os.path.basename(obj.file.name))
        assert suffix_match is not None
        suffix = suffix_match.group(1)

        try:
            assert obj.closed is True
            assert (
                obj.get_file_name() == "files/{}/Doc{}.pdf".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert (
                obj.get_file_url() == "/media/files/{}/Doc{}.pdf".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()
            obj.delete()

    def test_file_rename(self):
        with open(str(TESTS_PATH / "sheet.xlsx"), "rb") as xlsx_file:
            obj = UploadedFile(
                owner_app_label="app",
                owner_model_name="page",
                owner_fieldname="file",
            )
            obj.attach_file(xlsx_file)
            obj.save()

        old_name = obj.get_file_name()

        try:
            # check old file
            assert obj.get_file().storage.exists(old_name)
            assert obj.is_file_exists()

            obj.rename_file('new_name')

            # recheck old file
            assert obj.get_file().storage.exists(old_name)

            # check new file
            new_name = obj.get_file_name()
            assert obj.name == 'new_name'
            assert 'new_name.xlsx' in new_name
            assert obj.is_file_exists()
            assert obj.get_file().storage.exists(new_name)
        finally:
            obj.get_file().storage.delete(old_name)
            obj.delete_file()
            obj.delete()


class TestFileField:
    def test_rel(self):
        field = FileField()
        assert field.null is True
        assert field.related_model == 'paper_uploads.UploadedFile'
        assert field.postprocess is None

    def test_validators(self):
        field = FileField(
            validators=[
                validators.SizeValidator(10 * 1024 * 1024),
                validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
                validators.MimetypeValidator(['image/jpeg', 'image/bmp', 'image/Png']),
            ]
        )
        field.contribute_to_class(Page, 'file')

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
