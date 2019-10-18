from django.test import TestCase
from tests.app.models import Page
from ..variations import PaperVariation


class TestVariations(TestCase):
    def test_varaition_defaults(self):
        image_field = Page._meta.get_field('image_ext')
        variations = image_field.variations
        self.assertTrue(variations['tablet'].face_detection)
        self.assertDictEqual(
            variations['tablet'].extra_context['jpeg'],
            {
                'quality': 80,
                'progressive': True
            }
        )

    def test_varaition_defaults_override(self):
        image_field = Page._meta.get_field('image_ext')
        variations = image_field.variations
        self.assertDictEqual(
            variations['desktop'].extra_context['jpeg'],
            {
                'quality': 92
            }
        )

    def test_varaition_postprocess_disabled(self):
        variation = PaperVariation(
            size=(0, 0),
            postprocess=False
        )
        self.assertFalse(variation.get_postprocess_options('jpeg'))
        self.assertFalse(variation.get_postprocess_options('GIF'))
        self.assertFalse(variation.get_postprocess_options('svg'))

    def test_varaition_postprocess(self):
        variation = PaperVariation(
            size=(0, 0),
            postprocess=dict(
                jpeg={
                    'command': 'echo'
                },
                gif=False,
                webp={
                    'command': 'man'
                }
            )
        )
        self.assertDictEqual(
            variation.get_postprocess_options('jpeg'),
            {
                'command': 'echo',
            }
        )
        self.assertFalse(variation.get_postprocess_options('GIF'))
        self.assertIsNone(variation.get_postprocess_options('Tiff'))
        self.assertDictEqual(
            variation.get_postprocess_options('webp'),
            {
                'command': 'man',
            }
        )
