from pathlib import Path

import pytest

from ..models.fields import ImageField

TESTS_PATH = Path(__file__).parent / 'samples'


class TestImplicitVersions:
    def test_versions(self):
        field = ImageField(variations=dict(
            desktop=dict(
                size=(1920, 0),
                clip=False,
                versions=['webp'],
            ),
            tablet=dict(
                size=(1200, 0),
                clip=False,
                versions=['webp', '2x'],
            ),
            mobile=dict(
                size=(640, 0),
                clip=False,
                versions=['WebP', '2x', '3x', '4x'],
            ),
            webp_image=dict(
                size=(480, 0),
                format='webp',
                versions=['WEBP', '2x'],
            )
        ))

        assert set(field.variations.keys()) == {
            'desktop',
            'desktop_webp',
            'tablet',
            'tablet_webp',
            'tablet_2x',
            'tablet_webp_2x',
            'mobile',
            'mobile_webp',
            'mobile_2x',
            'mobile_webp_2x',
            'mobile_3x',
            'mobile_webp_3x',
            'mobile_4x',
            'mobile_webp_4x',
            'webp_image',
            'webp_image_2x',
        }

        for name, variation in field.variations.items():
            assert variation.name == name

        webp_variations = {
            'desktop_webp',
            'tablet_webp',
            'tablet_webp_2x',
            'mobile_webp',
            'mobile_webp_2x',
            'mobile_webp_3x',
            'mobile_webp_4x',
            'webp_image',
            'webp_image_2x',
        }
        non_webp_variations = {
            'desktop',
            'tablet',
            'tablet_2x',
            'mobile',
            'mobile_2x',
            'mobile_3x',
            'mobile_4x',
        }

        for name in webp_variations:
            assert field.variations[name].format == 'WEBP'

        for name in non_webp_variations:
            assert field.variations[name].format != 'WEBP'


class TestInvalidVersion:
    def test_invalid_versions(self) -> None:
        with pytest.raises(ValueError):
            ImageField(
                variations=dict(
                    desktop=dict(
                        size=(1920, 0),
                        clip=False,
                        versions=['webp', '1x', '7x'],
                    ),
                )
            )


class TestVersionOverride:
    def test_version_overwrite(self) -> None:
        field = ImageField(variations=dict(
            desktop_2x=dict(
                size=(1580, 0),
                clip=False,
            ),
            desktop=dict(
                size=(800, 0),
                clip=False,
                versions=['webp', '2x'],
            ),
        ))
        assert set(field.variations.keys()) == {
            'desktop',
            'desktop_webp',
            'desktop_2x',
            'desktop_webp_2x',
        }

        variation = field.variations['desktop_2x']
        assert variation.size == (1580, 0)
