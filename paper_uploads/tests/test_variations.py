from django.test import TestCase
from tests.app.models import Page


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