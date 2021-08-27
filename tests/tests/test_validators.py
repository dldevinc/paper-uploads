import os
import shutil
import tempfile

import pytest
from django.core.exceptions import ValidationError

from paper_uploads import validators
from .dummy import make_dummy_file, make_dummy_image


class TestExtensionValidator:
    def test_format_extension_list(self):
        validator = validators.ExtensionValidator(
            allowed=['jpg', 'Gif', 'jpeg', 'JPEG', 'PNG', 'gif', '.png', '.Jpg']
        )
        assert validator.allowed == ('jpg', 'gif', 'jpeg', 'png')

    def test_case_insensitive(self):
        validator = validators.ExtensionValidator(allowed=['Pdf'])
        with make_dummy_file('something.PDF') as fp:
            validator(fp)

    def test_fail(self):
        validator = validators.ExtensionValidator(allowed=['pdf'])
        with make_dummy_file('something.avi') as fp:
            with pytest.raises(ValidationError) as exc:
                validator(fp)

            assert (
                exc.value.messages[0] == "File `something.avi` has an invalid extension. "
                "Valid extension(s): pdf"
            )

    def test_custom_message(self):
        validator = validators.ExtensionValidator(allowed=['mp3'], message='invalid extension: %(ext)s')
        with pytest.raises(ValidationError) as exc:
            with make_dummy_file('something.pdf') as fp:
                validator(fp)
        assert (
            exc.value.messages[0] == "invalid extension: pdf"
        )

    def test_help_text(self):
        validator = validators.ExtensionValidator(allowed=['pdf', 'mp3'])
        assert str(validator.get_help_text()) == 'Allowed extensions: pdf, mp3'


class TestMimetypeValidator:
    def test_allowed_mimetypes(self):
        validator = validators.MimeTypeValidator(
            allowed=['image/*', 'video/mp4', 'video/ogg', 'image/jpg', 'Video/MP4']
        )
        assert validator.allowed == ('image/*', 'video/mp4', 'video/ogg', 'image/jpg')

    def test_case_insensitive(self):
        validator = validators.MimeTypeValidator(allowed=['iMaGe/Jpeg'])

        # dummy file with JPEG signature
        with make_dummy_file(content=b'\xff\xd8\xff') as fp:
            validator(fp)

    def test_asterisk(self):
        validator = validators.MimeTypeValidator(allowed=['image/*'])

        # dummy file with JPEG signature
        with make_dummy_file(content=b'\xff\xd8\xff') as fp:
            validator(fp)

    def test_fail(self):
        validator = validators.MimeTypeValidator(allowed=['image/*'])
        with make_dummy_file(content=b'Hello') as fp:
            with pytest.raises(ValidationError) as exc:
                validator(fp)

            assert (
                exc.value.messages[0]
                == "File `something.txt` has an invalid mimetype 'text/plain'"
            )

    def test_custom_message(self):
        validator = validators.MimeTypeValidator(allowed=['image/*'], message='invalid mimetype: %(mimetype)s')
        with pytest.raises(ValidationError) as exc:
            with make_dummy_file(content=b'Hello') as fp:
                validator(fp)
        assert (
            exc.value.messages[0] == "invalid mimetype: text/plain"
        )

    def test_help_text(self):
        validator = validators.MimeTypeValidator(allowed=['video/mp4', 'video/ogg', 'image/*'])
        assert str(validator.get_help_text()) == 'Allowed types: video/mp4, video/ogg, image/*'


class TestSizeValidator:
    def test_valid(self):
        validator = validators.SizeValidator(limit_value=8)
        for size in range(1, 9):
            with make_dummy_file(content=b'1234567890'[:size]) as fp:
                validator(fp)

    def test_fail(self):
        validator = validators.SizeValidator(limit_value=8)
        with pytest.raises(ValidationError) as exc:
            with make_dummy_file(content=b'123456789') as fp:
                validator(fp)

        assert (
            exc.value.messages[0]
            == "File `something.txt` is too large. Maximum file size is 8\xa0bytes."
        )

    def test_custom_message(self):
        validator = validators.SizeValidator(limit_value=2, message='invalid size: %(size)s')
        with pytest.raises(ValidationError) as exc:
            with make_dummy_file(content=b'Hello' * 1024) as fp:
                validator(fp)
        assert (
            exc.value.messages[0] == "invalid size: 5120"
        )

    def test_help_text(self):
        validator = validators.SizeValidator(limit_value=1024*1024)
        assert str(validator.get_help_text()) == 'Maximum file size: 1.0 MB'


class TestImageMinSizeValidator:
    def test_valid(self):
        validator = validators.ImageMinSizeValidator(40, 60)
        with make_dummy_image(width=40, height=60) as fp:
            validator(fp)
        with make_dummy_image(width=41, height=60) as fp:
            validator(fp)
        with make_dummy_image(width=40, height=61) as fp:
            validator(fp)

    def test_invalid_image(self):
        validator = validators.ImageMinSizeValidator(40, 60)
        with pytest.raises(ValidationError) as exc:
            with make_dummy_file(content=b'Hello') as fp:
                validator(fp)
        assert exc.value.messages[0] == "File `something.txt` is not an image"

    def test_closed_image(self):
        tfile = tempfile.NamedTemporaryFile(delete=False)
        shutil.copyfileobj(make_dummy_image(width=40, height=60), tfile)
        tfile.close()
        assert tfile.closed is True

        validator = validators.ImageMinSizeValidator(0, 0)

        with pytest.raises(ValidationError, match='is closed'):
            validator(tfile)

        os.unlink(tfile.name)

    def test_fail(self):
        validator = validators.ImageMinSizeValidator(40, 60)
        with pytest.raises(ValidationError) as exc:
            with make_dummy_image(width=39, height=60) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "Image `something.jpg` is not wide enough. The minimum width is 40 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with make_dummy_image(width=40, height=59) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "Image `something.jpg` is not tall enough. The minimum height is 60 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with make_dummy_image(width=39, height=59) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "Image `something.jpg` is too small. Image should be at least 40x60 pixels."
        )

    def test_help_text(self):
        validator = validators.ImageMinSizeValidator(640, 480)
        assert str(validator.get_help_text()) == 'Minimum dimensions: 640x480 pixels'

        validator = validators.ImageMinSizeValidator(640, 0)
        assert str(validator.get_help_text()) == 'Minimum image width: 640 pixels'

        validator = validators.ImageMinSizeValidator(0, 480)
        assert str(validator.get_help_text()) == 'Minimum image height: 480 pixels'


class TestImageMaxSizeValidator:
    def test_valid(self):
        validator = validators.ImageMaxSizeValidator(40, 60)
        with make_dummy_image(width=40, height=60) as fp:
            validator(fp)
        with make_dummy_image(width=39, height=60) as fp:
            validator(fp)
        with make_dummy_image(width=40, height=59) as fp:
            validator(fp)

    def test_invalid_image(self):
        validator = validators.ImageMaxSizeValidator(16, 24)
        with pytest.raises(ValidationError) as exc:
            with make_dummy_file(content=b'Hello') as fp:
                validator(fp)
        assert exc.value.messages[0] == "File `something.txt` is not an image"

    def test_closed_image(self):
        tfile = tempfile.NamedTemporaryFile(delete=False)
        shutil.copyfileobj(make_dummy_image(width=40, height=60), tfile)
        tfile.close()
        assert tfile.closed is True

        validator = validators.ImageMaxSizeValidator(0, 0)

        with pytest.raises(ValidationError, match='is closed'):
            validator(tfile)

        os.unlink(tfile.name)

    def test_fail(self):
        validator = validators.ImageMaxSizeValidator(40, 60)
        with pytest.raises(ValidationError) as exc:
            with make_dummy_image(width=40, height=61) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "Image `something.jpg` is too tall. The maximum height is 60 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with make_dummy_image(width=41, height=60) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "Image `something.jpg` is too wide. The maximum width is 40 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with make_dummy_image(width=41, height=61) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "Image `something.jpg` is too big. Image should be at most 40x60 pixels."
        )

    def test_help_text(self):
        validator = validators.ImageMaxSizeValidator(640, 480)
        assert str(validator.get_help_text()) == 'Maximum dimensions: 640x480 pixels'

        validator = validators.ImageMaxSizeValidator(640, 0)
        assert str(validator.get_help_text()) == 'Maximum image width: 640 pixels'

        validator = validators.ImageMaxSizeValidator(0, 480)
        assert str(validator.get_help_text()) == 'Maximum image height: 480 pixels'
