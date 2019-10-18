from pathlib import Path
from django.test import TestCase
from django.core.files import File
from ..exceptions import PostprocessProhibited
from .. import postprocess
from ..variations import PaperVariation
from ..models import *

TESTS_PATH = Path(__file__).parent / 'samples'


class TestCollection(Collection):
    svg = CollectionItemTypeField(SVGItem, postprocess=False)
    image = CollectionItemTypeField(ImageItem, postprocess=False, options={
        'variations': dict(
            mobile=dict(
                size=(640, 0),
                clip=False,
                postprocess={
                    'command': 'echo'
                }
            )
        )
    })
    file = CollectionItemTypeField(FileItem)


class TestGetOptions(TestCase):
    def test_global_options(self):
        self.assertDictEqual(
            postprocess.get_options('jpeg'),
            {
                'command': 'jpeg-recompress',
                'arguments': '--strip --quality medium "{file}" "{file}"',
            }
        )
        self.assertDictEqual(
            postprocess.get_options('png'),
            {
                'command': 'pngquant',
                'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
            }
        )
        self.assertDictEqual(
            postprocess.get_options('svg'),
            {
                'command': 'svgo',
                'arguments': '--precision=5 "{file}"',
            }
        )

    def test_unexisted_format(self):
        self.assertDictEqual(
            postprocess.get_options('exe'),
            {}
        )

    def test_case_insensitive(self):
        for format in ('jpeg', 'JPEG', 'Jpeg'):
            self.assertDictEqual(
                postprocess.get_options(format),
                {
                    'command': 'jpeg-recompress',
                    'arguments': '--strip --quality medium "{file}" "{file}"',
                }
            )

    def test_format_level_disabling(self):
        variation = PaperVariation(
            size=(0, 0),
            postprocess=dict(
                jpeg=False
            )
        )
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_options('jpeg', variation=variation)

    def test_variation_level_disabling(self):
        variation = PaperVariation(
            size=(0, 0),
            postprocess=False
        )
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_options('jpeg', variation=variation)
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_options('png', variation=variation)

    def test_global_level_disabling(self):
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_options('webp')

    def test_format_level_override(self):
        variation = PaperVariation(
            size=(0, 0),
            postprocess=dict(
                jpeg={
                    'command': 'echo'
                },
                webp={
                    'command': 'man'
                }
            )
        )
        self.assertDictEqual(
            postprocess.get_options('jpeg', variation=variation),
            {
                'command': 'echo',
            }
        )
        self.assertDictEqual(
            postprocess.get_options('webp', variation=variation),
            {
                'command': 'man',
            }
        )

    def test_collection_postrocess(self):
        svg_field = TestCollection.item_types['svg']
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_options('svg', field=svg_field)

    def test_collection_image_postrocess_issue(self):
        """
        Для картинок приоритет значения в поля окажется выше,
        чем значения в вариации.
        """
        image_field = TestCollection.item_types['svg']
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_options('jpeg', field=image_field)


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
