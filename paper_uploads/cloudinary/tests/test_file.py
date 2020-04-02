import re
from pathlib import Path
from datetime import timedelta

import cloudinary.uploader
import pytest
from django.template.defaultfilters import filesizeformat
from django.utils.timezone import now
from tests.app.models import Page

from ... import validators
from ..models import CloudinaryFile, CloudinaryFileField

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryFile:
    def test_file(self):
        with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as svg_file:
            obj = CloudinaryFile(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file',
            )
            obj.attach_file(svg_file, name='Cartman.SVG')
            obj.save()

        try:
            # Resource
            assert obj.name == 'Cartman'
            assert now() - obj.created_at < timedelta(seconds=10)
            assert now() - obj.uploaded_at < timedelta(seconds=10)
            assert now() - obj.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert obj.hash == '0de603d9b61a3af301f23a0f233113119f5368f5'

            # FileResource
            assert obj.extension == 'svg'
            assert obj.size == 1183
            assert str(obj) == 'Cartman.svg'
            assert repr(obj) == "CloudinaryFile('Cartman.svg')"
            assert obj.get_basename() == 'Cartman.svg'
            assert obj.get_file() is obj.file
            assert re.fullmatch(r'Cartman_\w+\.SVG', obj.get_file_name()) is not None
            assert (
                re.fullmatch(
                    r'http://res\.cloudinary\.com/[^/]+/raw/upload/[^/]+/Cartman_\w+\.SVG',
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
                assert obj.read(4) == b'<svg'
                assert obj.tell() == 4
                obj.seek(0)
                assert obj.tell() == 0
                assert obj.closed is False
            assert obj.closed is True

            with obj.open('r'):
                assert obj.read(4) == '<svg'

            # CloudinaryFileResource
            assert obj.cloudinary_resource_type == 'raw'
            assert obj.cloudinary_type == 'upload'

            cloudinary_field = obj._meta.get_field('file')
            assert cloudinary_field.type == obj.cloudinary_type
            assert cloudinary_field.resource_type == obj.cloudinary_resource_type

            obj.refresh_from_db()
            assert re.fullmatch(r'Cartman_\w+\.SVG', obj.get_public_id()) is not None

            # CloudinaryFile
            assert obj.display_name == 'Cartman'

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
        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            obj = CloudinaryFile()
            obj.attach_file(pdf_file, name='Doc.PDF')
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete_file()
            obj.delete()

    def test_empty_file(self):
        obj = CloudinaryFile(
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
        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            obj = CloudinaryFile(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file',
            )
            obj.attach_file(pdf_file, name='Doc.PDF')
            obj.save()

        cloudinary.uploader.destroy(
            obj.get_public_id(),
            type=obj.cloudinary_type,
            resource_type=obj.cloudinary_resource_type,
        )

        try:
            assert obj.closed is True
            assert re.fullmatch(r'Doc_\w+\.PDF', obj.get_file_name()) is not None
            assert (
                re.fullmatch(
                    r'http://res\.cloudinary\.com/[^/]+/raw/upload/[^/]+/Doc\w+\.PDF',
                    obj.get_file_url(),
                )
                is not None
            )
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()
            obj.delete()

    def test_file_rename(self):
        with open(str(TESTS_PATH / 'sheet.xlsx'), 'rb') as xlsx_file:
            obj = CloudinaryFile(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file',
            )
            obj.attach_file(xlsx_file)
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
            assert re.search(r'new_name_\w+\.xlsx$', obj.get_file_name()) is not None
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


class TestCloudinaryFileField:
    def test_rel(self):
        field = CloudinaryFileField()
        assert field.null is True
        assert field.related_model == 'paper_uploads_cloudinary.CloudinaryFile'

    def test_validators(self):
        field = CloudinaryFileField(
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
        field = CloudinaryFileField(cloudinary={
            'public_id': 'myfile',
            'folder': 'files',
        })
        assert field.cloudinary_options == {
            'public_id': 'myfile',
            'folder': 'files',
        }
