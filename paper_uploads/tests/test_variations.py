from tests.app.models import Page

from ..variations import PaperVariation


class TestVariations:
    def test_varaition_defaults(self):
        image_field = Page._meta.get_field('image_ext')
        variations = image_field.variations
        assert variations['tablet'].face_detection is True
        assert variations['tablet'].extra_context['jpeg'] == {
            'quality': 80,
            'progressive': True,
        }

    def test_varaition_defaults_override(self):
        image_field = Page._meta.get_field('image_ext')
        variations = image_field.variations
        assert variations['desktop'].extra_context['jpeg'] == {
            'quality': 92
        }

    def test_varaition_postprocess_disabled(self):
        variation = PaperVariation(
            size=(0, 0),
            postprocess=False
        )
        assert variation.get_postprocess_options('jpeg') is False
        assert variation.get_postprocess_options('GIF') is False
        assert variation.get_postprocess_options('svg') is False

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
        assert variation.get_postprocess_options('jpeg') == {
            'command': 'echo',
        }
        assert variation.get_postprocess_options('GIF') is False
        assert variation.get_postprocess_options('Tiff') is None
        assert variation.get_postprocess_options('webp') == {
            'command': 'man',
        }
