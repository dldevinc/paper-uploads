import pytest

from paper_uploads.variations import PaperVariation


class TestName:
    def test_default_value(self):
        variation = PaperVariation()
        assert variation.name == ''

    def test_invalid_type(self):
        with pytest.raises(TypeError):
            PaperVariation(name=42)


class TestOutputFileName:
    def test_unnamed(self):
        with pytest.raises(RuntimeError):
            PaperVariation().get_output_filename('source.Jpeg')

    def test_auto_format(self):
        variation = PaperVariation(name='desktop')
        assert variation.get_output_filename('source.Jpeg') == 'source.desktop.jpg'

    def test_forced_format(self):
        variation = PaperVariation(name='desktop', format='webp')
        assert variation.get_output_filename('source.Jpeg') == 'source.desktop.webp'
