from django.test import TestCase
from variations.variation import Variation
from ..exceptions import PostprocessProhibited
from .. import postprocess
from ..models import *


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
                'arguments': '--strip --quality medium --method smallfry "{file}" "{file}"',
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
                    'arguments': '--strip --quality medium --method smallfry "{file}" "{file}"',
                }
            )

    def test_format_level_disabling(self):
        variation = Variation(
            size=(0, 0),
            jpeg=dict(
                postprocess=False
            )
        )
        with self.assertRaises(PostprocessProhibited):
            postprocess.get_options('jpeg', variation=variation)

    def test_variation_level_disabling(self):
        variation = Variation(
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
        variation = Variation(
            size=(0, 0),
            jpeg=dict(
                postprocess={
                    'command': 'echo'
                }
            ),
            webp=dict(
                postprocess={
                    'command': 'man'
                }
            ),
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
