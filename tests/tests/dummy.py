import io
import os
from contextlib import contextmanager

from django.conf import settings
from django.core.files.base import File
from PIL import Image

from app.models import CompleteCollection
from paper_uploads.models.collection import *

NASA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/milky-way-nasa.jpg')
CALLIPHORA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/calliphora.jpg')
NATURE_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/Nature Tree.Jpeg')
DOCUMENT_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/document.pdf')
MEDITATION_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/Meditation.svg')

__all__ = [
    'NASA_FILEPATH',
    'CALLIPHORA_FILEPATH',
    'NATURE_FILEPATH',
    'DOCUMENT_FILEPATH',
    'MEDITATION_FILEPATH',
    'make_dummy_file',
    'make_dummy_image',
    'make_collection',
]


def make_dummy_file(name='something.txt', content=None):
    stream = File(io.BytesIO(), name=name)
    if content is not None:
        stream.write(content)
        stream.seek(0)
    return stream


def make_dummy_image(name='something.jpg', width=640, height=480):
    stream = File(io.BytesIO(), name=name)
    with Image.new('RGB', (width, height)) as img:
        img.save(stream, format='JPEG')
    stream.seek(0)
    return stream


@contextmanager
def make_collection(model=None, extra_file=True, images=True, svg=True):
    model = model or CompleteCollection
    collection = model.objects.create()

    file_item = FileItem()
    file_item.attach_to(collection)
    with open(DOCUMENT_FILEPATH, 'rb') as fp:
        file_item.attach_file(fp, name='collection_file1.pdf')
    file_item.save()

    if extra_file:
        file_item = FileItem()
        file_item.attach_to(collection)
        with open(CALLIPHORA_FILEPATH, 'rb') as fp:
            file_item.attach_file(fp, name='collection_file2.jpg')
        file_item.save()

    if images:
        image_item = ImageItem()
        image_item.attach_to(collection)
        with open(NATURE_FILEPATH, 'rb') as fp:
            image_item.attach_file(fp, name='collection_image1.jpg')
        image_item.save()

    if svg:
        svg_item = SVGItem()
        svg_item.attach_to(collection)
        with open(MEDITATION_FILEPATH, 'rb') as fp:
            svg_item.attach_file(fp, name='collection_svg1.svg')
        svg_item.save()

    yield collection

    for item in collection.items.all():
        item.delete_file()
        item.delete()
    collection.delete()
