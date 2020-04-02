import os
import re
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.timezone import now
from tests.app.models import Page

from .. import validators
from ..models import ImageField, UploadedImage, VariationFile

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestUploadedImage:
    def test_image(self):
        with open(str(TESTS_PATH / "Image.Jpeg"), "rb") as jpeg_file:
            obj = UploadedImage(
                title='Image title',
                description='Image description',
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='image_ext',
            )
            obj.attach_file(jpeg_file, name="Image.Jpeg")
            obj.save()

        suffix_match = re.match(r"Image((?:_\w+)?)", os.path.basename(obj.file.name))
        assert suffix_match is not None
        suffix = suffix_match.group(1)

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
            assert (
                obj.get_file_name() == "images/{}/Image{}.jpg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert (
                obj.get_file_url() == "/media/images/{}/Image{}.jpg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert obj.is_file_exists() is True

            # FileFieldResource
            assert os.path.isfile(obj.path)
            assert all(
                os.path.isfile(vfile.path) for vname, vfile in obj.variation_files()
            )

            # PostrocessableFileFieldResource
            assert os.stat(str(TESTS_PATH / 'Image.Jpeg')).st_size == 214779

            # ReverseFieldModelMixin
            assert obj.owner_app_label == 'app'
            assert obj.owner_model_name == 'page'
            assert obj.owner_fieldname == 'image_ext'
            assert obj.get_owner_model() is Page
            assert obj.get_owner_field() is Page._meta.get_field('image_ext')

            # ReadonlyFileProxyMixin
            assert obj.url == obj.get_file_url()
            assert obj.path == os.path.join(
                settings.BASE_DIR, settings.MEDIA_ROOT, obj.get_file_name()
            )
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
                'tablet': 82419,
                'admin': 13396,
            }

            for vname, vfile in obj.variation_files():
                assert os.path.isfile(vfile.path)
                assert os.stat(vfile.path).st_size == expected_varaition_sizes[vname]

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
                    size=filesizeformat(obj.size),
                ),
            }
        finally:
            source_path = obj.path
            variation_pathes = {vfile.path for vname, vfile in obj.variation_files()}

            obj.delete_file()
            assert os.path.isfile(source_path) is False
            assert all(not os.path.isfile(path) for path in variation_pathes)
            assert obj.is_file_exists() is False

    def test_orphan_image(self):
        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_image:
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
        with open(str(TESTS_PATH / 'Sample Document.PDF'), 'rb') as pdf_file:
            obj = UploadedImage()
            with pytest.raises(ValidationError) as exc:
                obj.attach_file(pdf_file, name='Doc.PDF')
            assert exc.value.message == '`Doc.pdf` is not an image'
            obj.delete_file()

    def test_empty_file(self):
        obj = UploadedImage(
            owner_app_label="app",
            owner_model_name="page",
            owner_fieldname="image_ext",
        )
        try:
            assert obj.closed is True
            assert bool(obj.file) is False
            with pytest.raises(ValueError):
                obj.get_file_url()
            assert obj.is_file_exists() is False
            assert obj.get_variation_file("desktop") is None
        finally:
            obj.delete_file()

    def test_missing_file(self):
        with open(str(TESTS_PATH / "Image.Jpeg"), "rb") as jpeg_file:
            obj = UploadedImage(
                owner_app_label='app',
                owner_model_name='page',
                owner_fieldname='image_ext',
            )
            obj.attach_file(jpeg_file, name="Image.Jpeg")
            obj.save()

        suffix_match = re.match(r"Image((?:_\w+)?)", os.path.basename(obj.file.name))
        assert suffix_match is not None
        suffix = suffix_match.group(1)

        os.unlink(obj.path)
        for vname, vfile in obj.variation_files():
            os.unlink(vfile.path)

        try:
            assert obj.closed is True
            assert (
                obj.get_file_name() == "images/{}/Image{}.jpg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert (
                obj.get_file_url() == "/media/images/{}/Image{}.jpg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
            assert obj.is_file_exists() is False
            assert (
                obj.desktop.url == "/media/images/{}/Image{}.desktop.jpg".format(
                    now().strftime('%Y-%m-%d'),
                    suffix
                )
            )
        finally:
            obj.delete_file()
            obj.delete()

    def test_file_rename(self):
        with open(str(TESTS_PATH / "Image.Jpeg"), "rb") as jpeg_file:
            obj = UploadedImage(
                owner_app_label="app",
                owner_model_name="page",
                owner_fieldname="image",
            )
            obj.attach_file(jpeg_file)
            obj.save()

        old_name = obj.get_file_name()
        old_variations = {vfile.path for vname, vfile in obj.variation_files()}

        try:
            # check old files
            assert obj.get_file().storage.exists(old_name)
            assert obj.is_file_exists()
            assert all(os.path.isfile(path) for path in old_variations)

            obj.rename_file('new_name')

            # recheck old files
            assert obj.get_file().storage.exists(old_name)
            assert all(os.path.isfile(path) for path in old_variations)

            # check new files
            new_name = obj.get_file_name()
            new_variations = {vfile.path for vname, vfile in obj.variation_files()}
            assert obj.name == 'new_name'
            assert 'new_name.jpg' in new_name
            assert obj.is_file_exists()
            assert obj.get_file().storage.exists(new_name)
            assert all(os.path.isfile(path) for path in new_variations)
        finally:
            obj.file.storage.delete(old_name)
            for path in old_variations:
                obj.file.storage.delete(path)

            obj.delete_file()
            obj.delete()


class TestImageField:
    def test_rel(self):
        field = ImageField()
        assert field.null is True
        assert field.related_model == 'paper_uploads.UploadedImage'

    def test_validators(self):
        field = ImageField(
            validators=[
                validators.SizeValidator(10 * 1024 * 1024),
                validators.ExtensionValidator(['svg', 'BmP', 'Jpeg']),
                validators.ImageMinSizeValidator(640, 480),
                validators.ImageMaxSizeValidator(1920, 1440),
            ]
        )
        field.contribute_to_class(Page, 'image')  # resets varaitions

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
