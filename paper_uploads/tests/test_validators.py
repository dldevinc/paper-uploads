import io
import os
import tempfile

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import File
from PIL import Image

from .. import validators


def dummy_file(name):
    return File(io.BytesIO(), name=name)


class TestExtensionValidator:
    def test_allowed_extensions(self):
        validator = validators.ExtensionValidator(
            allowed=['jpg', 'Gif', 'jpeg', 'JPEG', 'PNG', 'gif', '.png', '.Jpg']
        )
        assert validator.allowed == ('jpg', 'gif', 'jpeg', 'png')

    def test_case_insensitive(self):
        validator = validators.ExtensionValidator(allowed=['Pdf'])
        with dummy_file('something.PDF') as fp:
            validator(fp)

    def test_fail(self):
        validator = validators.ExtensionValidator(allowed=['pdf'])
        with dummy_file('something.avi') as fp:
            with pytest.raises(ValidationError) as exc:
                validator(fp)

            assert (
                exc.value.messages[0] == "`something.avi` has an invalid extension. "
                "Valid extension(s): pdf"
            )

    def test_custom_message(self):
        validator = validators.ExtensionValidator(allowed=['mp3'], message='invalid extension: %(ext)s')
        with pytest.raises(ValidationError) as exc:
            with dummy_file('something.pdf') as fp:
                validator(fp)
        assert (
            exc.value.messages[0] == "invalid extension: pdf"
        )


class TestMimetypeValidator:
    def test_allowed_mimetypes(self):
        validator = validators.MimetypeValidator(
            allowed=['image/*', 'video/mp4', 'video/ogg', 'image/jpg', 'Video/MP4']
        )
        assert validator.allowed == ('image/*', 'video/mp4', 'video/ogg', 'image/jpg')

    def test_case_insensitive(self):
        validator = validators.MimetypeValidator(allowed=['iMaGe/Jpeg'])
        with dummy_file('something.exe') as fp:
            fp.write(b'\xff\xd8\xff')  # JPEG signature
            fp.seek(0)
            validator(fp)

    def test_asterisk(self):
        validator = validators.MimetypeValidator(allowed=['image/*'])
        with dummy_file('something.exe') as fp:
            fp.write(b'\xff\xd8\xff')  # JPEG signature
            fp.seek(0)
            validator(fp)

    def test_fail(self):
        validator = validators.MimetypeValidator(allowed=['image/*'])
        with dummy_file('something.doc') as fp:
            fp.write(b'Hello')
            fp.seek(0)

            with pytest.raises(ValidationError) as exc:
                validator(fp)

            assert (
                exc.value.messages[0]
                == "`something.doc` has an invalid mimetype 'text/plain'"
            )

    def test_custom_message(self):
        validator = validators.MimetypeValidator(allowed=['image/*'], message='invalid mimetype: %(mimetype)s')
        with pytest.raises(ValidationError) as exc:
            with dummy_file('something.pdf') as fp:
                fp.write(b'Hello')
                fp.seek(0)
                validator(fp)
        assert (
            exc.value.messages[0] == "invalid mimetype: text/plain"
        )


class TestSizeValidator:
    def _make_file(self, content, stream=None):
        if stream is None:
            stream = dummy_file('something.jpg')
        stream.write(content)
        stream.seek(0)
        return stream

    def test_valid(self):
        validator = validators.SizeValidator(limit_value=8)
        for size in range(1, 9):
            with self._make_file(b'1234567890'[:size]) as fp:
                validator(fp)

    def test_fail(self):
        validator = validators.SizeValidator(limit_value=8)
        with pytest.raises(ValidationError) as exc:
            with self._make_file(b'123456789') as fp:
                validator(fp)

        assert (
            exc.value.messages[0]
            == "`something.jpg` is too large. Maximum file size is 8\xa0bytes."
        )

    def test_custom_message(self):
        validator = validators.SizeValidator(limit_value=2, message='invalid size: %(size)s')
        with pytest.raises(ValidationError) as exc:
            with dummy_file('something.pdf') as fp:
                fp.write(b'Hello' * 1024)
                fp.seek(0)
                validator(fp)
        assert (
            exc.value.messages[0] == "invalid size: 5120"
        )


class TestImageMinSizeValidator:
    def _make_image(self, width, height, stream=None):
        if stream is None:
            stream = dummy_file('something.jpg')
        with Image.new('RGB', (width, height)) as img:
            img.save(stream, format='JPEG')
        stream.seek(0)
        return stream

    def test_valid(self):
        validator = validators.ImageMinSizeValidator(16, 24)
        with self._make_image(16, 24) as fp:
            validator(fp)
        with self._make_image(24, 24) as fp:
            validator(fp)
        with self._make_image(16, 32) as fp:
            validator(fp)

    def test_invalid_image(self):
        validator = validators.ImageMinSizeValidator(16, 24)
        with pytest.raises(ValidationError) as exc:
            with dummy_file('something.jpg') as fp:
                fp.write(b'Hello')
                fp.seek(0)
                validator(fp)
        assert exc.value.messages[0] == "`something.jpg` is not an image"

    def test_closed_image(self):
        tfile = tempfile.NamedTemporaryFile(delete=False)
        self._make_image(32, 32, stream=tfile)
        tfile.close()
        assert tfile.closed is True

        validator = validators.ImageMinSizeValidator(0, 0)

        with pytest.raises(ValidationError, match='is closed'):
            validator(tfile)

        os.unlink(tfile.name)

    def test_fail(self):
        validator = validators.ImageMinSizeValidator(16, 24)
        with pytest.raises(ValidationError) as exc:
            with self._make_image(15, 24) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "`something.jpg` is not wide enough. Minimum width is 16 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with self._make_image(16, 23) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "`something.jpg` is not tall enough. Minimum height is 24 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with self._make_image(12, 16) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "`something.jpg` is too small. Image should be at least 16x24 pixels."
        )


class TestImageMaxSizeValidator:
    def _make_image(self, width, height, stream=None):
        if stream is None:
            stream = dummy_file('something.jpg')
        with Image.new('RGB', (width, height)) as img:
            img.save(stream, format='JPEG')
        stream.seek(0)
        return stream

    def test_valid(self):
        validator = validators.ImageMaxSizeValidator(16, 24)
        with self._make_image(16, 24) as fp:
            validator(fp)
        with self._make_image(15, 24) as fp:
            validator(fp)
        with self._make_image(16, 23) as fp:
            validator(fp)

    def test_invalid_image(self):
        validator = validators.ImageMaxSizeValidator(16, 24)
        with pytest.raises(ValidationError) as exc:
            with dummy_file('something.jpg') as fp:
                fp.write(b'Hello')
                fp.seek(0)
                validator(fp)
        assert exc.value.messages[0] == "`something.jpg` is not an image"

    def test_closed_image(self):
        tfile = tempfile.NamedTemporaryFile(delete=False)
        self._make_image(32, 32, stream=tfile)
        tfile.close()
        assert tfile.closed is True

        validator = validators.ImageMaxSizeValidator(0, 0)

        with pytest.raises(ValidationError, match='is closed'):
            validator(tfile)

        os.unlink(tfile.name)

    def test_fail(self):
        validator = validators.ImageMaxSizeValidator(16, 24)
        with pytest.raises(ValidationError) as exc:
            with self._make_image(16, 25) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "`something.jpg` is too tall. Maximum height is 24 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with self._make_image(17, 24) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "`something.jpg` is too wide. Maximum width is 16 pixels."
        )

        with pytest.raises(ValidationError) as exc:
            with self._make_image(640, 480) as fp:
                validator(fp)
        assert (
            exc.value.messages[0]
            == "`something.jpg` is too big. Image should be at most 16x24 pixels."
        )
