import re
import os
import pytest
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import now, timedelta
from django.template.defaultfilters import filesizeformat
from .. import validators
from ..models import VariationFile, UploadedImage, ImageField
from tests.app.models import Page

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestUploadedImage:
    def test_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = UploadedImage(
                title='Image title',
                description='Image description',
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='image_ext'
            )
            obj.attach_file(jpeg_file, name='Image.Jpeg')
            obj.save()

        suffix = re.match(r'Image((?:_\w+)?)', os.path.basename(obj.file.name)).group(1)

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
            assert repr(obj) == "UploadedImage('Image.jpg')"
            assert obj.get_basename() == 'Image.jpg'
            assert obj.get_file() is obj.file
            assert obj.get_file_name() == f"images/{now().strftime('%Y-%m-%d')}/Image{suffix}.jpg"
            assert obj.get_file_url() == f"/media/images/{now().strftime('%Y-%m-%d')}/Image{suffix}.jpg"
            assert obj.is_file_exists() is True

            # FileFieldResource
            assert os.path.isfile(obj.path)

            # PostrocessableFileFieldResource
            assert os.stat(TESTS_PATH / 'Image.Jpeg').st_size == 214779

            # ReverseFieldModelMixin
            assert obj.owner_app_label == 'app'
            assert obj.owner_model_name == 'page'
            assert obj.owner_fieldname == 'image_ext'
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('image_ext')

            # ReadonlyFileProxyMixin
            assert obj.url == obj.get_file_url()
            assert obj.path == os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, obj.get_file_name())
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

            # VariableImageResourceMixin
            assert obj.get_variations().keys() == {'desktop', 'tablet', 'admin'}

            assert obj._variations_attached is False
            assert isinstance(obj.get_variation_file('desktop'), VariationFile)
            assert obj.desktop is obj.get_variation_file('desktop')
            assert obj._variations_attached is True

            for vname, vfile in obj.variation_files():
                assert isinstance(vfile, VariationFile)
                assert vfile is obj.get_variation_file(vname)

            assert obj.calculate_max_size((3000, 2000)) == (1600, 1067)
            assert obj.calculate_max_size((1600, 1000)) == (1600, 1000)
            assert obj.calculate_max_size((1400, 1200)) == (1600, 1200)
            assert obj.calculate_max_size((800, 600)) == (1600, 600)

            expected_varaition_sizes = {
                'desktop': 137100,
                'tablet': 82449,
                'admin': 13404,
            }
            varaition_dir = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, f"images/{now().strftime('%Y-%m-%d')}/")
            for vname in obj.get_variations().keys():
                file_path = os.path.join(varaition_dir, f"Image{suffix}.{vname}.jpg")
                assert os.path.isfile(file_path)
                assert os.stat(file_path).st_size == expected_varaition_sizes[vname]

            with pytest.raises(KeyError):
                obj.get_variation_file('nothing')

            # UploadedImage
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
            file_path = obj.path
            assert os.path.isfile(file_path) is True
            obj.delete_file()
            assert os.path.isfile(file_path) is False
            assert obj.is_file_exists() is False

            varaition_dir = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, f"images/{now().strftime('%Y-%m-%d')}/")
            for vname in obj.get_variations().keys():
                file_path = os.path.join(varaition_dir, f"Image{suffix}.{vname}.jpg")
                assert os.path.isfile(file_path) is False

    def test_orphan_image(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_image:
            obj = UploadedImage()
            obj.attach_file(jpeg_image, name='Image.Jpeg')
            obj.save()

        try:
            assert obj.get_owner_model() is None
            assert obj.get_owner_field() is None
        finally:
            obj.delete_file()
            obj.delete()

    def test_not_image(self):
        with open(TESTS_PATH / 'Sample Document.PDF', 'rb') as pdf_file:
            obj = UploadedImage()
            with pytest.raises(ValidationError) as exc:
                obj.attach_file(pdf_file, name='Doc.PDF')
            assert exc.value.message == '`Doc.pdf` is not an image'
            obj.delete_file()

    def test_empty_file(self):
        obj = UploadedImage()
        try:
            assert obj.closed is True
            assert obj.get_file_name() == ''
            with pytest.raises(ValueError):
                obj.get_file_url()
            assert obj.is_file_exists() is False
        finally:
            obj.delete_file()

    def test_missing_file(self):
        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as jpeg_file:
            obj = UploadedImage(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='image_ext'
            )
            obj.attach_file(jpeg_file, name='Image.Jpeg')
            obj.save()

        suffix = re.match(r'Image((?:_\w+)?)', os.path.basename(obj.file.name)).group(1)

        os.unlink(obj.path)
        varaition_dir = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, f"images/{now().strftime('%Y-%m-%d')}/")
        for vname in obj.get_variations().keys():
            file_path = os.path.join(varaition_dir, f"Image{suffix}.{vname}.jpg")
            os.unlink(file_path)

        try:
            assert obj.closed is True
            assert obj.get_file_name() == f"images/{now().strftime('%Y-%m-%d')}/Image{suffix}.jpg"
            assert obj.get_file_url() == f"/media/images/{now().strftime('%Y-%m-%d')}/Image{suffix}.jpg"
            assert obj.is_file_exists() is False
            assert obj.desktop.url == f"/media/images/{now().strftime('%Y-%m-%d')}/Image{suffix}.desktop.jpg"
        finally:
            obj.delete_file()
            obj.delete()


class TestImageField:
    def test_rel(self):
        field = ImageField()
        assert field.null is True
        assert field.related_model == 'paper_uploads.UploadedImage'

    def test_validators(self):
        field = ImageField(validators=[
            validators.SizeValidator(10 * 1024 * 1024),
            validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
            validators.ImageMinSizeValidator(640, 480),
            validators.ImageMaxSizeValidator(1920, 1440),
        ])
        field.contribute_to_class(Page, 'image')    # resets varaitions

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
