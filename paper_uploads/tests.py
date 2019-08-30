import os
from django.test import TestCase
from django.core.files import File

TESTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests'))


class TestFiles(TestCase):
    def test_file_upload(self):
        from .models import UploadedFile

        file = UploadedFile(
            file=File(
                open(os.path.join(TESTS_PATH, 'small.pdf'), 'rb'),
                name='bubuka.PDF'
            ),
        )
        file.save()
        try:
            self.assertEqual(file.name, 'bubuka')
            self.assertEqual(file.extension, 'pdf')
            self.assertEqual(file.size, 9678)
            self.assertEqual(file.hash, 'bebc2ddd2a8b8270b359990580ff346d14c021fa')
            self.assertEqual(file.canonical_name, 'bubuka.pdf')
            self.assertTrue(os.path.isfile(file.path))
        finally:
            file.delete()

    def test_image_upload(self):
        from .models import UploadedImage

        image = UploadedImage(
            file=File(
                open(os.path.join(TESTS_PATH, 'image.jpg'), 'rb'),
                name='the car.JPEG'
            ),
        )
        image.save()
        try:
            self.assertEqual(image.name, 'the car')
            self.assertEqual(image.extension, 'jpeg')
            self.assertEqual(image.size, 214779)
            self.assertEqual(image.width, 1600)
            self.assertEqual(image.height, 1200)
            self.assertEqual(image.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')
            self.assertEqual(image.canonical_name, 'the car.jpeg')
            self.assertTrue(os.path.isfile(image.path))
        finally:
            image.delete()

    def test_gallery_proxy_inheritance(self):
        from .models import Gallery

        class TestGallery(Gallery):
            pass

        self.assertTrue(TestGallery._meta.proxy)

    def test_gallery_file(self):
        from .models import Gallery, GalleryFileItem

        class TestGallery(Gallery):
            pass

        gallery = TestGallery.objects.create()
        try:
            item = GalleryFileItem(
                file=File(
                    open(os.path.join(TESTS_PATH, 'small.pdf'), 'rb'),
                    name='bubuka.PDF'
                ),
            )
            item.attach_to(gallery, 'file')
            self.assertEqual(item.name, 'bubuka')
            self.assertEqual(item.extension, 'pdf')
            self.assertEqual(item.size, 9678)
            self.assertEqual(item.hash, 'bebc2ddd2a8b8270b359990580ff346d14c021fa')
            self.assertEqual(item.canonical_name, 'bubuka.pdf')
            self.assertEqual(item.item_type, 'file')
            self.assertEqual(item.preview, '/static/paper_uploads/dist/image/pdf.svg')
            self.assertTrue(os.path.isfile(item.path))
        finally:
            gallery.delete()

    def test_gallery_image(self):
        from .models import Gallery, GalleryImageItem

        class TestGallery(Gallery):
            VARIATIONS = dict(
                foo=dict(
                    size=(100, 100)
                )
            )

        gallery = TestGallery.objects.create()
        try:
            item = GalleryImageItem(
                file=File(
                    open(os.path.join(TESTS_PATH, 'image.jpg'), 'rb'),
                    name='the car.JPEG'
                ),
            )
            item.attach_to(gallery, 'image')
            self.assertEqual(item.name, 'the car')
            self.assertEqual(item.extension, 'jpeg')
            self.assertEqual(item.size, 214779)
            self.assertEqual(item.width, 1600)
            self.assertEqual(item.height, 1200)
            self.assertEqual(item.hash, '8af6d51189e57d1e6ae4188a5a1fcaea4da39b7b')
            self.assertEqual(item.canonical_name, 'the car.jpeg')
            self.assertEqual(item.item_type, 'image')
            self.assertTrue(os.path.isfile(item.path))
        finally:
            gallery.delete()
