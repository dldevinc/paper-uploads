import os

import pytest
from django.core.files import File
from django.template.loader import render_to_string

from app.models import (
    CloudinaryCompleteCollection,
    CloudinaryFileCollection,
    CloudinaryMediaCollection,
    CloudinaryPhotoCollection,
)
from paper_uploads.cloudinary.models import (
    CloudinaryFileItem,
    CloudinaryImageItem,
    CloudinaryMediaItem,
)

from ... import utils
from ...dummy import *
from ...models.test_collection import TestCollectionItem


class TestFileItem(TestCollectionItem):
    resource_name = 'document'
    resource_extension = 'pdf'
    resource_size = 3028
    resource_hash = '93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e'
    file_field_name = 'file'
    collection_class = CloudinaryFileCollection

    @classmethod
    def init(cls, storage):
        storage.collection = cls.collection_class.objects.create()

        storage.resource = CloudinaryFileItem()
        storage.resource.attach_to(storage.collection)
        with open(DOCUMENT_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()

        yield

        storage.resource.delete_file()
        storage.resource.delete()
        storage.collection.delete()

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_name

    def test_path(self, storage):
        pass

    def test_open(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(4) == b'%PDF'

    def test_close(self, storage):
        assert storage.resource.closed is True
        with storage.resource.open():
            assert storage.resource.closed is False
        assert storage.resource.closed is True

    def test_get_file_name(self, storage):
        file_name = storage.resource.get_file_name()
        assert file_name == utils.get_target_filepath(
            'collections/files/%Y-%m-%d/document{suffix}.pdf',
            file_name
        )

    def test_get_file_url(self, storage):
        file_url = storage.resource.get_file_url()
        assert file_url.startswith('https://res.cloudinary.com/')

    def test_url(self, storage):
        assert storage.resource.url.startswith('https://res.cloudinary.com/')

    def test_as_dict(self, storage):
        assert storage.resource.as_dict() == {
            'id': 1,
            'collectionId': 1,
            'item_type': 'file',
            'name': self.resource_name,
            'extension': self.resource_extension,
            'size': self.resource_size,
            'caption': '{}.{}'.format(self.resource_name, self.resource_extension),
            'url': storage.resource.get_file_url(),
            'preview': render_to_string(
                'paper_uploads/collection_item/preview/file.html',
                storage.resource.get_preview_context()
            )
        }


# class TestFileItemFilesExists:
#     @staticmethod
#     def init(storage):
#         storage.collection = FileCollection.objects.create()
#
#         storage.resource = FileItem()
#         storage.resource.attach_to(storage.collection)
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp)
#         storage.resource.save()
#
#         yield
#
#         try:
#             storage.resource.delete_file()
#         except ValueError:
#             pass
#
#         storage.resource.delete()
#         storage.collection.delete()
#
#     def test_files(self, storage):
#         source_path = storage.resource.path
#         assert os.path.exists(source_path) is True
#         storage.resource.delete_file()
#         assert os.path.exists(source_path) is False
#
#
# class TestFileItemRename(TestFileRename):
#     @classmethod
#     def init(cls, storage):
#         storage.collection = FileCollection.objects.create()
#
#         storage.resource = FileItem()
#         storage.resource.attach_to(storage.collection)
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp, name='old_name.jpg')
#         storage.resource.save()
#
#         file = storage.resource.get_file()
#         storage.old_source_name = file.name
#         storage.old_source_path = file.path
#         storage.resource.rename_file('new_name.png')
#
#         yield
#
#         os.remove(storage.old_source_path)
#         storage.resource.delete_file()
#         storage.resource.delete()
#
#     def test_old_file_name(self, storage):
#         assert storage.old_source_name == utils.get_target_filepath(
#             'collections/files/%Y-%m-%d/old_name{suffix}.jpg',
#             storage.old_source_name
#         )
#
#     def test_new_file_name(self, storage):
#         file = storage.resource.get_file()
#         assert file.name == utils.get_target_filepath(
#             'collections/files/%Y-%m-%d/new_name{suffix}.png',
#             file.name
#         )
#
#
# class TestFileItemDelete(TestFileDelete):
#     @classmethod
#     def init(cls, storage):
#         storage.collection = FileCollection.objects.create()
#
#         storage.resource = FileItem()
#         storage.resource.attach_to(storage.collection)
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp, name='old_name.jpg')
#         storage.resource.save()
#
#         file = storage.resource.get_file()
#         storage.old_source_name = file.name
#         storage.old_source_path = file.path
#         storage.resource.delete_file()
#
#         yield
#
#         storage.resource.delete()
#
#     def test_file_name(self, storage):
#         assert storage.old_source_name == utils.get_target_filepath(
#             'collections/files/%Y-%m-%d/old_name{suffix}.jpg',
#             storage.old_source_name
#         )
#
#
# class TestEmptyFileItem(TestEmptyFileFieldResource):
#     @classmethod
#     def init(cls, storage):
#         storage.resource = FileItem()
#         yield
#
#
# class TestSVGItem(TestCollectionItem):
#     resource_name = 'Meditation'
#     resource_extension = 'svg'
#     resource_size = 47193
#     resource_hash = '7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d'
#     file_field_name = 'file'
#     collection_class = CompleteCollection
#
#     @classmethod
#     def init(cls, storage):
#         storage.collection = cls.collection_class.objects.create()
#
#         storage.resource = SVGItem()
#         storage.resource.attach_to(storage.collection)
#         with open(MEDITATION_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp)
#         storage.resource.save()
#
#         yield
#
#         storage.resource.delete_file()
#         storage.resource.delete()
#         storage.collection.delete()
#
#     def test_get_file_name(self, storage):
#         file_name = storage.resource.get_file_name()
#         assert file_name == utils.get_target_filepath(
#             'collections/files/%Y-%m-%d/Meditation{suffix}.svg',
#             file_name
#         )
#
#     def test_get_file_url(self, storage):
#         file_url = storage.resource.get_file_url()
#         assert file_url == utils.get_target_filepath(
#             '/media/collections/files/%Y-%m-%d/Meditation{suffix}.svg',
#             file_url
#         )
#
#     def test_path(self, storage):
#         assert storage.resource.path.endswith(utils.get_target_filepath(
#             '/media/collections/files/%Y-%m-%d/Meditation{suffix}.svg',
#             storage.resource.get_file_url()
#         ))
#
#     def test_url(self, storage):
#         assert storage.resource.url == utils.get_target_filepath(
#             '/media/collections/files/%Y-%m-%d/Meditation{suffix}.svg',
#             storage.resource.get_file_url()
#         )
#
#     def test_item_type(self, storage):
#         assert storage.resource.item_type == 'svg'
#
#     def test_as_dict(self, storage):
#         assert storage.resource.as_dict() == {
#             'id': 1,
#             'collectionId': 1,
#             'item_type': 'svg',
#             'name': self.resource_name,
#             'extension': self.resource_extension,
#             'size': self.resource_size,
#             'caption': '{}.{}'.format(self.resource_name, self.resource_extension),
#             'url': utils.get_target_filepath(
#                 '/media/collections/files/%Y-%m-%d/Meditation{suffix}.svg',
#                 storage.resource.get_file_url()
#             ),
#             'preview': render_to_string(
#                 'paper_uploads/collection_item/preview/svg.html',
#                 storage.resource.get_preview_context()
#             )
#         }
#
#     def test_open(self, storage):
#         with storage.resource.open() as fp:
#             assert fp.read(5) == b'<?xml'
#
#         storage.resource.open()  # reopen
#
#     def test_file_supported(self, storage):
#         with open(DOCUMENT_FILEPATH, 'rb') as fp:
#             assert storage.resource.file_supported(File(fp)) is False
#
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             assert storage.resource.file_supported(File(fp)) is False
#
#         with open(MEDITATION_FILEPATH, 'rb') as fp:
#             assert storage.resource.file_supported(File(fp)) is True
#
#
# class TestSVGItemFilesExists:
#     @classmethod
#     def init(cls, storage):
#         storage.collection = CompleteCollection.objects.create()
#
#         storage.resource = SVGItem()
#         storage.resource.attach_to(storage.collection)
#         with open(MEDITATION_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp)
#         storage.resource.save()
#
#         yield
#
#         try:
#             storage.resource.delete_file()
#         except ValueError:
#             pass
#
#         storage.resource.delete()
#         storage.collection.delete()
#
#     def test_files(self, storage):
#         source_path = storage.resource.path
#         assert os.path.exists(source_path) is True
#         storage.resource.delete_file()
#         assert os.path.exists(source_path) is False
#
#
# class TestSVGItemRename(TestFileRename):
#     @classmethod
#     def init(cls, storage):
#         storage.collection = CompleteCollection.objects.create()
#
#         storage.resource = SVGItem()
#         storage.resource.attach_to(storage.collection)
#         with open(MEDITATION_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp, name='old_name.jpg')
#         storage.resource.save()
#
#         file = storage.resource.get_file()
#         storage.old_source_name = file.name
#         storage.old_source_path = file.path
#         storage.resource.rename_file('new_name.png')
#
#         yield
#
#         os.remove(storage.old_source_path)
#         storage.resource.delete_file()
#         storage.resource.delete()
#
#     def test_old_file_name(self, storage):
#         assert storage.old_source_name == utils.get_target_filepath(
#             'collections/files/%Y-%m-%d/old_name{suffix}.jpg',
#             storage.old_source_name
#         )
#
#     def test_new_file_name(self, storage):
#         file = storage.resource.get_file()
#         assert file.name == utils.get_target_filepath(
#             'collections/files/%Y-%m-%d/new_name{suffix}.png',
#             file.name
#         )
#
#
# class TestSVGItemDelete(TestFileDelete):
#     @classmethod
#     def init(cls, storage):
#         storage.collection = CompleteCollection.objects.create()
#
#         storage.resource = SVGItem()
#         storage.resource.attach_to(storage.collection)
#         with open(MEDITATION_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp, name='old_name.jpg')
#         storage.resource.save()
#
#         file = storage.resource.get_file()
#         storage.old_source_name = file.name
#         storage.old_source_path = file.path
#         storage.resource.delete_file()
#
#         yield
#
#         storage.resource.delete()
#
#     def test_file_name(self, storage):
#         assert storage.old_source_name == utils.get_target_filepath(
#             'collections/files/%Y-%m-%d/old_name{suffix}.jpg',
#             storage.old_source_name
#         )
#
#
# class TestEmptySVGItem(TestEmptyFileFieldResource):
#     @classmethod
#     def init(cls, storage):
#         storage.resource = SVGItem()
#         yield
#
#
# class TestImageItem(TestCollectionItem):
#     resource_name = 'Nature Tree'
#     resource_extension = 'jpg'
#     resource_size = 672759
#     resource_hash = 'e3a7f0318daaa395af0b84c1bca249cbfd46b9994b0aceb07f74332de4b061e1'
#     file_field_name = 'file'
#     collection_class = CompleteCollection
#
#     @classmethod
#     def init(cls, storage):
#         storage.collection = cls.collection_class.objects.create()
#
#         storage.resource = ImageItem()
#         storage.resource.attach_to(storage.collection)
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp)
#         storage.resource.save()
#
#         yield
#
#         storage.resource.delete_file()
#         storage.resource.delete()
#         storage.collection.delete()
#
#     def test_get_file_name(self, storage):
#         file_name = storage.resource.get_file_name()
#         assert file_name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/Nature_Tree{suffix}.jpg',
#             file_name
#         )
#
#     def test_get_file_url(self, storage):
#         file_url = storage.resource.get_file_url()
#         assert file_url == utils.get_target_filepath(
#             '/media/collections/images/%Y-%m-%d/Nature_Tree{suffix}.jpg',
#             file_url
#         )
#
#     def test_path(self, storage):
#         assert storage.resource.path.endswith(utils.get_target_filepath(
#             '/media/collections/images/%Y-%m-%d/Nature_Tree{suffix}.jpg',
#             storage.resource.get_file_url()
#         ))
#
#     def test_url(self, storage):
#         assert storage.resource.url == utils.get_target_filepath(
#             '/media/collections/images/%Y-%m-%d/Nature_Tree{suffix}.jpg',
#             storage.resource.get_file_url()
#         )
#
#     def test_item_type(self, storage):
#         assert storage.resource.item_type == 'image'
#
#     def test_as_dict(self, storage):
#         assert storage.resource.as_dict() == {
#             'id': 1,
#             'collectionId': 1,
#             'item_type': 'image',
#             'name': self.resource_name,
#             'extension': self.resource_extension,
#             'size': self.resource_size,
#             'width': 1534,
#             'height': 2301,
#             'cropregion': '',
#             'title': '',
#             'description': '',
#             'caption': '{}.{}'.format(self.resource_name, self.resource_extension),
#             'url': utils.get_target_filepath(
#                 '/media/collections/images/%Y-%m-%d/Nature_Tree{suffix}.jpg',
#                 storage.resource.get_file_url()
#             ),
#             'preview': render_to_string(
#                 'paper_uploads/collection_item/preview/image.html',
#                 storage.resource.get_preview_context()
#             )
#         }
#
#     def test_get_variations(self, storage):
#         variations = storage.resource.get_variations()
#         for name in storage.resource.PREVIEW_VARIATIONS:
#             assert name in variations
#
#     def test_width(self, storage):
#         assert storage.resource.width == 1534
#
#     def test_height(self, storage):
#         assert storage.resource.height == 2301
#
#     def test_file_supported(self, storage):
#         with open(DOCUMENT_FILEPATH, 'rb') as fp:
#             assert storage.resource.file_supported(File(fp)) is False
#
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             assert storage.resource.file_supported(File(fp)) is True
#
#         # SVG passes image test
#         with open(MEDITATION_FILEPATH, 'rb') as fp:
#             assert storage.resource.file_supported(File(fp)) is True
#
#
# class TestImageItemFilesExists:
#     @classmethod
#     def init(cls, storage):
#         storage.collection = CompleteCollection.objects.create()
#
#         storage.resource = ImageItem()
#         storage.resource.attach_to(storage.collection)
#         with open(NASA_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp)
#         storage.resource.save()
#
#         yield
#
#         try:
#             storage.resource.delete_file()
#         except ValueError:
#             pass
#
#         storage.resource.delete()
#         storage.collection.delete()
#
#     def test_files(self, storage):
#         source_path = storage.resource.path
#         desktop_path = storage.resource.desktop.path
#         mobile_path = storage.resource.mobile.path
#
#         assert os.path.exists(source_path) is True
#         assert os.path.exists(desktop_path) is True
#         assert os.path.exists(mobile_path) is True
#
#         storage.resource.delete_file()
#
#         assert os.path.exists(source_path) is False
#         assert os.path.exists(desktop_path) is False
#         assert os.path.exists(mobile_path) is False
#
#
# class TestImageItemRename(TestImageRename):
#     @classmethod
#     def init(cls, storage):
#         storage.collection = CompleteCollection.objects.create()
#
#         storage.resource = ImageItem()
#         storage.resource.attach_to(storage.collection)
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp, name='old_name.jpg')
#         storage.resource.save()
#
#         file = storage.resource.get_file()
#         storage.old_source_name = file.name
#         storage.old_desktop_name = storage.resource.desktop.name
#         storage.old_mobile_name = storage.resource.mobile.name
#
#         storage.old_source_path = file.path
#         storage.old_desktop_path = storage.resource.desktop.path
#         storage.old_mobile_path = storage.resource.mobile.path
#
#         storage.resource.rename_file('new_name.png')
#
#         yield
#
#         os.remove(storage.old_source_path)
#         os.remove(storage.old_desktop_path)
#         os.remove(storage.old_mobile_path)
#         storage.resource.delete_file()
#         storage.resource.delete()
#
#     def test_old_file_name(self, storage):
#         assert storage.old_source_name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/old_name{suffix}.jpg',
#             storage.old_source_name
#         )
#         assert storage.old_desktop_name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/old_name{suffix}.desktop.jpg',
#             storage.old_source_name
#         )
#         assert storage.old_mobile_name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/old_name{suffix}.mobile.jpg',
#             storage.old_source_name
#         )
#
#     def test_new_file_name(self, storage):
#         file = storage.resource.get_file()
#         assert file.name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/new_name{suffix}.png',
#             file.name
#         )
#         assert storage.resource.desktop.name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/new_name{suffix}.desktop.png',
#             file.name
#         )
#         assert storage.resource.mobile.name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/new_name{suffix}.mobile.png',
#             file.name
#         )
#
#
# class TestImageItemDelete(TestImageDelete):
#     @classmethod
#     def init(cls, storage):
#         storage.collection = CompleteCollection.objects.create()
#
#         storage.resource = ImageItem()
#         storage.resource.attach_to(storage.collection)
#         with open(NATURE_FILEPATH, 'rb') as fp:
#             storage.resource.attach_file(fp, name='old_name.jpg')
#         storage.resource.save()
#
#         file = storage.resource.get_file()
#         storage.old_source_name = file.name
#         storage.old_desktop_name = storage.resource.desktop.name
#         storage.old_mobile_name = storage.resource.mobile.name
#
#         storage.old_source_path = file.path
#         storage.old_desktop_path = storage.resource.desktop.path
#         storage.old_mobile_path = storage.resource.mobile.path
#
#         storage.resource.delete_file()
#
#         yield
#
#         storage.resource.delete()
#
#     def test_file_name(self, storage):
#         assert storage.old_source_name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/old_name{suffix}.jpg',
#             storage.old_source_name
#         )
#         assert storage.old_desktop_name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/old_name{suffix}.desktop.jpg',
#             storage.old_source_name
#         )
#         assert storage.old_mobile_name == utils.get_target_filepath(
#             'collections/images/%Y-%m-%d/old_name{suffix}.mobile.jpg',
#             storage.old_source_name
#         )
#
#
# class TestEmptyImageItem(TestEmptyVersatileImageResource):
#     @classmethod
#     def init(cls, storage):
#         storage.resource = ImageItem()
#         yield
