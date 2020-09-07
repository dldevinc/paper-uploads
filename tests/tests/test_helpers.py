import io

import pytest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import File
from PIL import Image
from variations import processors

from app.models import DummyResource
from paper_uploads import helpers, validators


class TestGetFilename:
    def test_camelcase(self):
        assert helpers.get_filename('/tmp/folder/File Name.JpEg') == 'File Name'

    def test_no_extension(self):
        assert helpers.get_filename('/tmp/file') == 'file'


class TestGetExtensions:
    def test_camelcase(self):
        assert helpers.get_extension('/tmp/folder/File Name.JpEg') == 'JpEg'

    def test_no_extension(self):
        assert helpers.get_extension('/tmp/file') == ''


class TestBuildVariations:
    variations = None

    def setup(self):
        from paper_uploads.conf import settings

        old_setting = settings.VARIATION_DEFAULTS
        settings.VARIATION_DEFAULTS = dict(
            size=(640, 480),
            jpeg=dict(
                quality=92,
                progressive=True
            ),
            webp=dict(
                lossless=True,
                quality=90,
            ),
            postprocessors=[
                processors.ColorOverlay('#FF0000', overlay_opacity=0.25),
            ],
        )

        self.variations = helpers.build_variations(
            dict(
                desktop=dict(
                    size=(1600, 0),
                    clip=False,
                    postprocessors=[],
                    jpeg=dict(
                        quality=80,
                    ),
                ),
                tablet=dict(
                    size=(1024, 0),
                    clip=False,
                    versions={'webp', '2x'},
                    jpeg=dict(
                        quality=75,
                    ),
                ),
                tablet_webp=dict(
                    size=(1200, 0),
                    clip=False,
                    format='WEBP',
                    webp=dict(
                        quality=60,
                    ),
                ),
                mobile=dict(
                    size=(640, 0),
                    clip=False,
                ),
            )
        )

        # restore option
        settings.VARIATION_DEFAULTS = old_setting

    def test_count(self):
        # 3 normal variations + 3 implicit for `tablet`
        assert len(self.variations) == 6

    def test_size_overriden(self):
        assert self.variations['desktop'].size == (1600, 0)
        assert self.variations['tablet'].size == (1024, 0)
        assert self.variations['mobile'].size == (640, 0)

    def test_extra_context_replaced(self):
        assert self.variations['desktop'].extra_context['jpeg'] == {
            'quality': 80,
        }
        assert self.variations['tablet'].extra_context['jpeg'] == {
            'quality': 75,
        }
        assert self.variations['mobile'].extra_context['jpeg'] == {
            'quality': 92,
            'progressive': True,
        }

    def test_postprocessors_replaced(self):
        assert self.variations['desktop'].postprocessors == []
        assert isinstance(
            self.variations['tablet'].postprocessors[0], processors.ColorOverlay
        )
        assert isinstance(
            self.variations['mobile'].postprocessors[0], processors.ColorOverlay
        )

    def test_names(self):
        assert self.variations['desktop'].name == 'desktop'
        assert self.variations['tablet'].name == 'tablet'
        assert self.variations['mobile'].name == 'mobile'
        assert self.variations['tablet_webp'].name == 'tablet_webp'
        assert self.variations['tablet_2x'].name == 'tablet_2x'
        assert self.variations['tablet_webp_2x'].name == 'tablet_webp_2x'

    def test_retina_size(self):
        assert self.variations['tablet_2x'].size == (2048, 0)
        assert self.variations['tablet_webp_2x'].size == (2048, 0)

    def test_webp_format(self):
        assert self.variations['tablet_2x'].format == 'AUTO'
        assert self.variations['tablet_webp'].format == 'WEBP'
        assert self.variations['tablet_webp_2x'].format == 'WEBP'

    def test_explicit_overwrite_version(self):
        assert self.variations['tablet_webp'].size == (1200, 0)
        assert self.variations['tablet_webp'].extra_context['webp']['quality'] == 60

    def test_invalid_versions(self):
        with pytest.raises(ValueError):
            helpers.build_variations(dict(
                demo=dict(
                    versions={'2x', '7x', 'png'}
                )
            ))


class TestImplicitVariations:
    variations = None

    def setup(self):
        self.variations = helpers.build_variations(
            dict(
                tablet=dict(
                    upscale=True,
                    anchor='br',
                    versions={'webp', '2x', '3x', '4x'},
                ),
            )
        )

    def test_count(self):
        # 1 normal variations + 7 implicit for `tablet`
        assert len(self.variations) == 8

    def test_names(self):
        assert self.variations['tablet'].name == 'tablet'
        assert self.variations['tablet_webp'].name == 'tablet_webp'
        assert self.variations['tablet_2x'].name == 'tablet_2x'
        assert self.variations['tablet_3x'].name == 'tablet_3x'
        assert self.variations['tablet_4x'].name == 'tablet_4x'
        assert self.variations['tablet_webp_2x'].name == 'tablet_webp_2x'
        assert self.variations['tablet_webp_3x'].name == 'tablet_webp_3x'
        assert self.variations['tablet_webp_4x'].name == 'tablet_webp_4x'

    def test_shared_params(self):
        for varaition in self.variations.values():
            assert varaition.upscale is True
            assert varaition.anchor == (1, 1)


@pytest.mark.django_db
def test_get_instance():
    resource = DummyResource.objects.create(id=1)

    assert helpers.get_instance('app', 'dummyresource', 1) == resource
    assert helpers.get_instance('app', 'dummyresource', 1, using='default') == resource

    with pytest.raises(ObjectDoesNotExist):
        assert helpers.get_instance('app', 'dummyresource', 2)


def test_run_validators():
    with File(io.BytesIO(), name='file.jpeg') as file:
        with Image.new('RGB', (640, 480)) as img:
            img.save(file, format='JPEG')

        try:
            helpers.run_validators(
                file,
                [
                    validators.ExtensionValidator(['jpg']),
                    validators.ImageMinSizeValidator(800, 600),
                    validators.ImageMaxSizeValidator(1024, 800),
                ],
            )
        except ValidationError as exc:
            assert len(exc.messages) == 2
            assert (
                "has an invalid extension. Valid extension(s): jpg" in exc.messages[0]
            )
            assert (
                "is too small. Image should be at least 800x600 pixels."
                in exc.messages[1]
            )
