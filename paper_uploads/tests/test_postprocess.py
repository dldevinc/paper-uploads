from pathlib import Path
from django.test import TestCase
from django.core.files import File
from tests.app.models import TestCollection, TestCollectionBlocked, TestCollectionOverride
from ..exceptions import PostprocessProhibited
from .. import postprocess
from ..variations import PaperVariation
from ..models import *

TESTS_PATH = Path(__file__).parent / 'samples'


class TestGlobalPostprocessOptions(TestCase):
    def test_jpeg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_common_options('jpeg'),
            {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }
        )

    def test_png_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_common_options('png'),
            {
                'command': 'pngquant',
                'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
            }
        )

    def test_svg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_common_options('svg'),
            {
                'command': 'svgo',
                'arguments': '--precision=5 "{file}"',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe')

    def test_case_insensitive(self):
        for format in ('jpeg', 'JPEG', 'Jpeg'):
            self.assertDictEqual(
                postprocess.get_postprocess_common_options(format),
                {
                    'command': 'jpeg-recompress',
                    'arguments': '--strip --quality medium "{file}" "{file}"',
                }
            )


class TestVariationPostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.variation = PaperVariation(
            size=(1920, 0)
        )

    def test_jpeg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('jpeg', self.variation),
            {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }
        )

    def test_png_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('png', self.variation),
            {
                'command': 'pngquant',
                'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
            }
        )

    def test_svg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('svg', self.variation),
            {
                'command': 'svgo',
                'arguments': '--precision=5 "{file}"',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', self.variation)

    def test_case_insensitive(self):
        for format in ('jpeg', 'JPEG', 'Jpeg'):
            self.assertDictEqual(
                postprocess.get_postprocess_variation_options(format, self.variation),
                {
                    'command': 'jpeg-recompress',
                    'arguments': '--strip --quality medium "{file}" "{file}"',
                }
            )


class TestVariationBlockedPostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.variation = PaperVariation(
            size=(1920, 0),
            postprocess=False
        )

    def test_jpeg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('jpeg', self.variation)

    def test_png_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('png', self.variation)

    def test_svg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('svg', self.variation)

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', self.variation)


class TestVariationOverridePostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.variation = PaperVariation(
            size=(1920, 0),
            postprocess=dict(
                jpeg=False,
                svg={
                    'command': 'echo'
                }
            )
        )

    def test_jpeg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('jpeg', self.variation)

    def test_png_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('png', self.variation),
            {
                'command': 'pngquant',
                'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
            }
        )

    def test_svg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('svg', self.variation),
            {
                'command': 'echo',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', self.variation)


class TestFileFieldPostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.field = FileField()

    def test_svg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_common_options('svg', field=self.field),
            {
                'command': 'svgo',
                'arguments': '--precision=5 "{file}"',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field=self.field)

    def test_case_insensitive(self):
        for format in ('svg', 'SVG', 'Svg'):
            self.assertDictEqual(
                postprocess.get_postprocess_common_options(format),
                {
                    'command': 'svgo',
                    'arguments': '--precision=5 "{file}"',
                }
            )


class TestFileFieldBlockedPostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.field = FileField(postprocess=False)

    def test_svg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field=self.field)

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field=self.field)


class TestFileFieldOverridePostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.field = FileField(postprocess=dict(
            svg=False,
            exe={
                'command': 'echo'
            }
        ))

    def test_svg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field=self.field)

    def test_exe_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_common_options('exe', field=self.field),
            {
                'command': 'echo',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('mp3', field=self.field)


class TestCollectionFilePostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.field = CollectionItemTypeField(SVGItem)

    def test_svg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_common_options('svg', field=self.field),
            {
                'command': 'svgo',
                'arguments': '--precision=5 "{file}"',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field=self.field)


class TestCollectionFileBlockedPostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.field = CollectionItemTypeField(SVGItem, postprocess=False)

    def test_svg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field=self.field)

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('exe', field=self.field)


class TestCollectionFileOverridePostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.field = CollectionItemTypeField(SVGItem, postprocess=dict(
            svg=False,
            exe={
                'command': 'echo'
            }
        ))

    def test_svg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('svg', field=self.field)

    def test_exe_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_common_options('exe', field=self.field),
            {
                'command': 'echo',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_common_options('mp3', field=self.field)


class TestCollectionPostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.collection = TestCollection.objects.create()
        self.field = TestCollection.item_types['image']

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.item = ImageItem(
                file=File(fp, name='Image.Jpeg'),
                alt='Alternate text',
                title='Image title',
            )
            self.item.attach_to(self.collection)
            self.item.full_clean()
            self.item.save()

        self.variation = self.item.get_variations()['mobile']

    def tearDown(self) -> None:
        self.collection.delete()

    def test_jpeg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('jpeg', self.variation, field=self.field),
            {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }
        )

    def test_png_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('png', self.variation, field=self.field),
            {
                'command': 'pngquant',
                'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
            }
        )

    def test_svg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('svg', self.variation, field=self.field),
            {
                'command': 'svgo',
                'arguments': '--precision=5 "{file}"',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', self.variation, field=self.field)

    def test_case_insensitive(self):
        for format in ('jpeg', 'JPEG', 'Jpeg'):
            self.assertDictEqual(
                postprocess.get_postprocess_variation_options(format, self.variation, field=self.field),
                {
                    'command': 'jpeg-recompress',
                    'arguments': '--strip --quality medium "{file}" "{file}"',
                }
            )

    def test_item_postprocessed(self):
        self.assertEqual(self.item.mobile.size, 89900)


class TestCollectionBlockedPostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.collection = TestCollectionBlocked.objects.create()
        self.field = TestCollectionBlocked.item_types['image']

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.item = ImageItem(
                file=File(fp, name='Image.Jpeg'),
                alt='Alternate text',
                title='Image title',
            )
            self.item.attach_to(self.collection)
            self.item.full_clean()
            self.item.save()

        self.variation = self.item.get_variations()['mobile']

    def tearDown(self) -> None:
        self.collection.delete()

    def test_jpeg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('jpeg', self.variation, field=self.field)

    def test_png_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('png', self.variation, field=self.field)

    def test_svg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('svg', self.variation, field=self.field)

    def test_webp_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('webp', self.variation, field=self.field),
            {
                'command': 'echo',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', self.variation, field=self.field)

    def test_item_not_postprocessed(self):
        self.assertEqual(self.item.mobile.size, 109101)


class TestCollectionOverridePostprocessOptions(TestCase):
    def setUp(self) -> None:
        self.collection = TestCollectionOverride.objects.create()
        self.field = TestCollectionOverride.item_types['image']

        with open(TESTS_PATH / 'Image.Jpeg', 'rb') as fp:
            self.item = ImageItem(
                file=File(fp, name='Image.Jpeg'),
                alt='Alternate text',
                title='Image title',
            )
            self.item.attach_to(self.collection)
            self.item.full_clean()
            self.item.save()

        self.variation = self.item.get_variations()['mobile']

    def tearDown(self) -> None:
        self.collection.delete()

    def test_jpeg_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('jpeg', self.variation, field=self.field)

    def test_png_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('png', self.variation, field=self.field),
            {
                'command': 'echo',
            }
        )

    def test_svg_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('svg', self.variation, field=self.field),
            {
                'command': 'svgo',
                'arguments': '--precision=5 "{file}"',
            }
        )

    def test_webp_options(self):
        self.assertDictEqual(
            postprocess.get_postprocess_variation_options('webp', self.variation, field=self.field),
            {
                'command': 'man',
            }
        )

    def test_unknown_options(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_postprocess_variation_options('exe', self.variation, field=self.field)

    def test_item_not_postprocessed(self):
        self.assertEqual(self.item.mobile.size, 109101)


class TestFilePostprocess(TestCase):
    def setUp(self) -> None:
        with open(TESTS_PATH / 'cartman.svg', 'rb') as fp:
            self.object = UploadedFile(
                file=File(fp, name='cartman.svg'),
            )
            self.object.save()

    def tearDown(self) -> None:
        self.object.delete()

    def test_file_size(self):
        self.assertEqual(self.object.size, 1022)

    def test_file_hash(self):
        self.assertEqual(self.object.hash, 'f98668ff3534d61cfcef507478abfe7b4c1dbb8a')
