import pytest

from paper_uploads.variations import PaperVariation


class TestName:
    def test_default_value(self):
        variation = PaperVariation()
        assert variation.name == ''

    def test_invalid_type(self):
        with pytest.raises(TypeError):
            PaperVariation(name=42)


class TestPostprocess:
    def test_default_value(self):
        variation = PaperVariation()
        assert variation.postprocess is None

    def test_false_value(self):
        variation = PaperVariation(postprocess=False)
        assert variation.postprocess is False

    def test_dict_value(self):
        variation = PaperVariation(
            postprocess={
                'JpeG': {'command': 'echo'}
            }
        )

        # keys lowercased
        assert variation.postprocess == {
            'jpeg': {'command': 'echo'}
        }

    def test_invalid_type(self):
        with pytest.raises(TypeError):
            PaperVariation(postprocess='False')


class TestOuptputFileName:
    def test_unnamed(self):
        with pytest.raises(RuntimeError):
            PaperVariation().get_output_filename('source.Jpeg')

    def test_auto_format(self):
        variation = PaperVariation(name='desktop')
        assert variation.get_output_filename('source.Jpeg') == 'source.desktop.jpg'

    def test_forced_format(self):
        variation = PaperVariation(name='desktop', format='webp')
        assert variation.get_output_filename('source.Jpeg') == 'source.desktop.webp'
