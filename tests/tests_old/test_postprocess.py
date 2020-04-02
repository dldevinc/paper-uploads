from pathlib import Path

import pytest
from tests.app.models import (
    DummyCollection,
    DummyCollectionPostprocessProhibited,
    DummyCollectionOverride,
)

from .. import postprocess
from ..exceptions import PostprocessProhibited
from ..models.collection import ImageItem, SVGItem
from ..models.fields import FileField, ItemField
from ..models.file import UploadedFile
from ..variations import PaperVariation

pytestmark = pytest.mark.django_db
TESTS_PATH = Path(__file__).parent / 'samples'


class TestGlobal:
    def test_options(self):
        assert postprocess.get_postprocess_common_options('jpeg') == {
            'command': 'jpeg-recompress',
            'arguments': '--strip --quality medium "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_common_options('png') == {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_common_options('svg') == {
            'command': 'svgo',
            'arguments': '--precision=4 --disable=convertPathData "{file}"',
        }

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe')

        for format in ('jpeg', 'JPEG', 'Jpeg'):
            assert postprocess.get_postprocess_common_options(format) == {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }


class TestVariation:
    def test_options(self):
        variation = PaperVariation(size=(1920, 0))

        assert postprocess.get_postprocess_variation_options('jpeg', variation) == {
            'command': 'jpeg-recompress',
            'arguments': '--strip --quality medium "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_variation_options('png', variation) == {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_variation_options('svg', variation) == {
            'command': 'svgo',
            'arguments': '--precision=4 --disable=convertPathData "{file}"',
        }

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', variation)

        for format in ('jpeg', 'JPEG', 'Jpeg'):
            assert postprocess.get_postprocess_variation_options(format, variation) == {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }


class TestVariationProhibited:
    def test_options(self):
        variation = PaperVariation(
            size=(1920, 0),
            postprocess=False
        )

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('jpeg', variation)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('png', variation)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('svg', variation)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', variation)

        for format in ('jpeg', 'JPEG', 'Jpeg'):
            with pytest.raises(PostprocessProhibited):
                postprocess.get_postprocess_variation_options(format, variation)


class TestVariationOverride:
    def test_options(self):
        variation = PaperVariation(
            size=(1920, 0),
            postprocess=dict(
                jpeg=False,
                svg={
                    'command': 'echo'
                }
            )
        )

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('jpeg', variation)

        assert postprocess.get_postprocess_variation_options('png', variation) == {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_variation_options('svg', variation) == {
            'command': 'echo',
        }

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', variation)

        for format in ('jpeg', 'JPEG', 'Jpeg'):
            with pytest.raises(PostprocessProhibited):
                postprocess.get_postprocess_variation_options(format, variation)


class TestFileField:
    def test_options(self):
        field = FileField()

        assert postprocess.get_postprocess_common_options('jpeg', field) == {
            'command': 'jpeg-recompress',
            'arguments': '--strip --quality medium "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_common_options('png', field) == {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_common_options('svg', field) == {
            'command': 'svgo',
            'arguments': '--precision=4 --disable=convertPathData "{file}"',
        }

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field)

        for format in ('jpeg', 'JPEG', 'Jpeg'):
            assert postprocess.get_postprocess_common_options(format, field) == {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }


class TestFileFieldProhibited:
    def test_options(self):
        field = FileField(postprocess=False)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('jpeg', field)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('png', field)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field)

        for format in ('jpeg', 'JPEG', 'Jpeg'):
            with pytest.raises(PostprocessProhibited):
                postprocess.get_postprocess_common_options(format, field)


class TestFileFieldOverride:
    def test_options(self):
        field = FileField(postprocess=dict(
            svg=False,
            exe={
                'command': 'echo'
            }
        ))

        assert postprocess.get_postprocess_common_options('jpeg', field) == {
            'command': 'jpeg-recompress',
            'arguments': '--strip --quality medium "{file}" "{file}"',
        }

        assert postprocess.get_postprocess_common_options('png', field) == {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"',
        }

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field)

        assert postprocess.get_postprocess_common_options('exe', field) == {
            'command': 'echo',
        }

        for format in ('jpeg', 'JPEG', 'Jpeg'):
            assert postprocess.get_postprocess_common_options(format, field) == {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }


class TestCollectionItemField:
    def test_options(self):
        field = ItemField(SVGItem)

        assert postprocess.get_postprocess_common_options('svg', field) == {
            'command': 'svgo',
            'arguments': '--precision=4 --disable=convertPathData "{file}"',
        }

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field)


class TestCollectionItemFieldProhibited:
    def test_options(self):
        field = ItemField(SVGItem, postprocess=False)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field)

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field)


class TestItemFieldOverride:
    def test_options(self):
        field = ItemField(SVGItem, postprocess=dict(
            svg=False,
            exe={
                'command': 'echo'
            }
        ))

        with pytest.raises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field)

        assert postprocess.get_postprocess_common_options('exe', field) == {
            'command': 'echo',
        }


class TestPostprocess:
    def test_options(self):
        with open(str(TESTS_PATH / 'cartman.svg'), 'rb') as fp:
            obj = UploadedFile()
            obj.attach_file(fp, name='cartman.svg')
            obj.save()

        try:
            assert obj.size == 1118
            assert obj.hash == '563bca379c51c21a7bdff080f7cff67914040c10'
        finally:
            obj.delete_file()
            obj.delete()


class TestRealCollection:
    def test_options(self):
        collection = DummyCollection.objects.create()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            item = ImageItem(
                title='Image title',
                description='Alternate text',
            )
            item.attach_to(collection)
            item.attach_file(jpeg_file)
            item.full_clean()
            item.save()

        variation = item.get_variations()['mobile']
        field = collection.item_types['image']

        try:
            assert postprocess.get_postprocess_variation_options(
                'jpeg', variation, field=field
            ) == {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }

            assert postprocess.get_postprocess_variation_options(
                'png', variation, field=field
            ) == {
                'command': 'pngquant',
                'arguments': '--force --skip-if-larger --output "{file}" "{file}"',
            }

            assert postprocess.get_postprocess_variation_options(
                'svg', variation, field=field
            ) == {
                'command': 'svgo',
                'arguments': '--precision=4 --disable=convertPathData "{file}"',
            }

            # ensure postprocessed
            assert item.mobile.size == 89900
        finally:
            item.delete_file()
            collection.delete()


class TestRealCollectionProhibited:
    def test_options(self):
        collection = DummyCollectionPostprocessProhibited.objects.create()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            item = ImageItem(
                title='Image title',
                description='Alternate text',
            )
            item.attach_to(collection)
            item.attach_file(jpeg_file)
            item.full_clean()
            item.save()

        variation = item.get_variations()['mobile']
        field = collection.item_types['image']

        try:
            with pytest.raises(PostprocessProhibited):
                postprocess.get_postprocess_variation_options(
                    'jpeg', variation, field=field
                )

            with pytest.raises(PostprocessProhibited):
                postprocess.get_postprocess_variation_options(
                    'png', variation, field=field
                )

            with pytest.raises(PostprocessProhibited):
                postprocess.get_postprocess_variation_options(
                    'svg', variation, field=field
                )

            assert postprocess.get_postprocess_variation_options(
                'webp', variation, field=field
            ) == {'command': 'echo'}

            # ensure not postprocessed
            assert item.mobile.size == 109015
        finally:
            item.delete_file()
            collection.delete()


class TestRealCollectionOverride:
    def test_options(self):
        collection = DummyCollectionOverride.objects.create()

        with open(str(TESTS_PATH / 'Image.Jpeg'), 'rb') as jpeg_file:
            item = ImageItem(
                title='Image title',
                description='Alternate text',
            )
            item.attach_to(collection)
            item.attach_file(jpeg_file)
            item.full_clean()
            item.save()

        variation = item.get_variations()['mobile']
        field = collection.item_types['image']

        try:
            with pytest.raises(PostprocessProhibited):
                postprocess.get_postprocess_variation_options(
                    'jpeg', variation, field=field
                )

            assert postprocess.get_postprocess_variation_options(
                'png', variation, field=field
            ) == {'command': 'echo'}

            assert postprocess.get_postprocess_variation_options(
                'svg', variation, field=field
            ) == {
                'command': 'svgo',
                'arguments': '--precision=4 --disable=convertPathData "{file}"',
            }

            assert postprocess.get_postprocess_variation_options(
                'webp', variation, field=field
            ) == {'command': 'man'}

            # ensure not postprocessed
            assert item.mobile.size == 109015
        finally:
            item.delete_file()
            collection.delete()
