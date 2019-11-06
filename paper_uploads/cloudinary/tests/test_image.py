import re
import pytest
from pathlib import Path
import cloudinary.uploader
from django.core.exceptions import ValidationError
from django.utils.timezone import now, timedelta
from django.template.defaultfilters import filesizeformat
from ... import validators
from ..models import CloudinaryImage, CloudinaryImageField
from tests.app.models import Page

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent.parent.parent / 'tests' / 'samples'


class TestCloudinaryImage:
    def test_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = CloudinaryImage(
                title='Image title',
                description='Image description',
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_image'
            )
            obj.attach_file(jpeg_file, name='Image.Jpeg')
            obj.save()

        try:
            # Resource
            assert obj.name == 'Image'
            assert now() - obj.created_at < timedelta(seconds=10)
            assert now() - obj.uploaded_at < timedelta(seconds=10)
            assert now() - obj.modified_at < timedelta(seconds=10)

            # HashableResourceMixin
            assert obj.hash == '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b'

            # FileResource
            assert obj.extension == 'jpg'
            assert obj.size == 214779
            assert str(obj) == 'Image.jpg'
            assert repr(obj) == "CloudinaryImage('Image.jpg')"
            assert obj.get_basename() == 'Image.jpg'
            assert obj.get_file() is obj.file
            assert re.fullmatch(r'Image_\w+\.jpg', obj.get_file_name()) is not None
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/image/upload/[^/]+/Image_\w+\.jpg', obj.get_file_url()) is not None
            assert obj.is_file_exists() is True

            # ReverseFieldModelMixin
            assert obj.owner_app_label == 'app'
            assert obj.owner_model_name == 'page'
            assert obj.owner_fieldname == 'cloud_image'
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('cloud_image')

            # ReadonlyFileProxyMixin
            assert obj.url == obj.get_file_url()

            with pytest.raises(AttributeError):
                print(obj.path)

            assert obj.closed is True
            with obj.open():
                assert obj.closed is False
                assert obj.read(4) == b'\xff\xd8\xff\xe0'
                assert obj.tell() == 4
                obj.seek(0)
                assert obj.tell() == 0
                assert obj.closed is False
            assert obj.closed is True

            # ImageFileResourceMixin
            assert obj.title == 'Image title'
            assert obj.description == 'Image description'
            assert obj.width == 1600
            assert obj.height == 1200
            assert obj.cropregion == ''

            # CloudinaryFileResource
            assert obj.cloudinary_resource_type == 'image'
            assert obj.cloudinary_type == 'upload'

            cloudinary_field = obj._meta.get_field('file')
            assert cloudinary_field.type == obj.cloudinary_type
            assert cloudinary_field.resource_type == obj.cloudinary_resource_type

            obj.refresh_from_db()
            assert re.fullmatch(r'Image_\w+', obj.get_public_id()) is not None

            assert obj.get_validation() == {
                'acceptFiles': ['image/*'],
            }

            # as_dict
            assert obj.as_dict() == {
                'id': obj.pk,
                'name': obj.name,
                'extension': obj.extension,
                'size': obj.size,
                'url': obj.get_file_url(),
                'width': obj.width,
                'height': obj.height,
                'cropregion': obj.cropregion,
                'title': obj.title,
                'description': obj.description,
                'file_info': '({ext}, {width}x{height}, {size})'.format(
                    ext=obj.extension,
                    width=obj.width,
                    height=obj.height,
                    size=filesizeformat(obj.size)
                )
            }
        finally:
            obj.delete_file()
            assert obj.is_file_exists() is False

            obj.delete()

    def test_orphan_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_image:
            obj = CloudinaryImage()
            obj.attach_file(jpeg_image, name='Image.Jpeg')
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete_file()
            obj.delete()

    def test_not_image(self):
        with open(TESTS_PATH / 'sheet.xlsx', 'rb') as pdf_file:
            obj = CloudinaryImage()
            with pytest.raises(ValidationError, match='Unsupported .*'):
                obj.attach_file(pdf_file)
            obj.delete_file()

    def test_empty_file(self):
        obj = CloudinaryImage()
        try:
            assert obj.closed is True
            assert bool(obj.file) is False
            with pytest.raises(AttributeError):
                obj.get_file_url()
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()

    def test_missing_file(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = CloudinaryImage(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_image'
            )
            obj.attach_file(jpeg_file, name='Image.Jpeg')
            obj.save()

        cloudinary.uploader.destroy(
            obj.get_public_id(),
            type=obj.cloudinary_type,
            resource_type=obj.cloudinary_resource_type
        )

        try:
            assert obj.closed is True
            assert re.fullmatch(r'Image\w+\.jpg', obj.get_file_name()) is not None
            assert re.fullmatch(r'http://res\.cloudinary\.com/[^/]+/image/upload/[^/]+/Image\w+\.jpg', obj.get_file_url()) is not None
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()
            obj.delete()

    def test_file_rename(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = CloudinaryImage(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='cloud_file'
            )
            obj.attach_file(jpeg_file)
            obj.save()

        old_name = obj.get_public_id()
        obj.rename_file('/path/to/new_image.rar')    # must use only filename without extension

        try:
            new_name = obj.get_public_id()
            assert 'new_image' in new_name
            assert obj.is_file_exists()
        finally:
            cloudinary.uploader.destroy(
                old_name,
                type=obj.cloudinary_type,
                resource_type=obj.cloudinary_resource_type
            )

            obj.delete_file()
            obj.delete()


class TestCloudinaryImageField:
    def test_rel(self):
        field = CloudinaryImageField()
        assert field.null is True
        assert field.related_model == 'paper_uploads_cloudinary.CloudinaryImage'

    def test_validators(self):
        field = CloudinaryImageField(validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
            validators.ImageMinSizeValidator(640, 480),
            validators.ImageMaxSizeValidator(1920, 1440),
        ])
        field.contribute_to_class(Page, 'cloud_image')    # resets varaitions

        assert field.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'minImageWidth': 640,
            'minImageHeight': 480,
            'maxImageWidth': 1920,
            'maxImageHeight': 1440,
        }

        formfield = field.formfield()
        assert formfield.widget.get_validation() == {
            'sizeLimit': 10 * 1024 * 1024,
            'allowedExtensions': ('svg', 'bmp', 'jpeg'),
            'acceptFiles': ['image/*'],
            'minImageWidth': 640,
            'minImageHeight': 480,
            'maxImageWidth': 1920,
            'maxImageHeight': 1440,
        }

    def test_cloudinary_options(self):
        field = CloudinaryImageField(cloudinary={
            'public_id': 'myimage',
            'folder': 'images',
        })
        assert field.cloudinary_options == {
            'public_id': 'myimage',
            'folder': 'images',
        }
