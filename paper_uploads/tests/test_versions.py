from pathlib import Path
from django.test import TestCase
from ..models.fields import ImageField

TESTS_PATH = Path(__file__).parent / 'samples'


class TestImplicitVersions(TestCase):
    def setUp(self) -> None:
        self.field = ImageField(variations=dict(
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
                versions=['WebP', '2x', '3x'],
            ),
            webp_image=dict(
                size=(480, 0),
                format='webp',
                versions=['WEBP', '2x'],
            )
        ))

    def test_implicit_variations(self):
        self.assertSetEqual(
            set(self.field.variations.keys()),
            {
                'desktop', 'desktop_webp',
                'tablet', 'tablet_webp', 'tablet_2x', 'tablet_webp_2x',
                'mobile', 'mobile_webp', 'mobile_2x', 'mobile_webp_2x', 'mobile_3x', 'mobile_webp_3x',
                'webp_image', 'webp_image_2x'
            }
        )

    def test_webp_versions(self):
        webp_variations = {
            'desktop_webp',
            'tablet_webp', 'tablet_webp_2x',
            'mobile_webp', 'mobile_webp_2x', 'mobile_webp_3x',
            'webp_image', 'webp_image_2x'
        }
        non_webp_variations = {
            'desktop',
            'tablet', 'tablet_2x',
            'mobile', 'mobile_2x', 'mobile_3x',
        }
        for name in webp_variations:
            with self.subTest(name):
                self.assertEqual(self.field.variations[name].format, 'WEBP')

        for name in non_webp_variations:
            with self.subTest(name):
                self.assertNotEqual(self.field.variations[name].format, 'WEBP')


class TestInvalidVersion(TestCase):
    def test_invalid_versions(self) -> None:
        with self.assertRaises(ValueError):
            self.field = ImageField(variations=dict(
                desktop=dict(
                    size=(1920, 0),
                    clip=False,
                    versions=['webp', '1x', '7x'],
                ),
            ))


class TestVersionOverride(TestCase):
    def setUp(self) -> None:
        self.field = ImageField(variations=dict(
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

    def test_implicit_variations(self):
        self.assertSetEqual(
            set(self.field.variations.keys()),
            {
                'desktop', 'desktop_webp', 'desktop_2x', 'desktop_webp_2x',
            }
        )

    def test_version_overwrite(self) -> None:
        variation = self.field.variations['desktop_2x']
        self.assertEqual(variation.size, (1580, 0))
