import io
import os

from django.conf import settings
from django.core.files.base import File
from PIL import Image

NASA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/milky-way-nasa.jpg')
CALLIPHORA_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/calliphora.jpg')
NATURE_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/Nature Tree.Jpeg')
DOCUMENT_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/document.pdf')
MEDITATION_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/Meditation.svg')
AUDIO_FILEPATH = os.path.join(settings.BASE_DIR, 'tests/samples/audio.mp3')

__all__ = [
    'NASA_FILEPATH',
    'CALLIPHORA_FILEPATH',
    'NATURE_FILEPATH',
    'DOCUMENT_FILEPATH',
    'MEDITATION_FILEPATH',
    'AUDIO_FILEPATH',
    'make_dummy_file',
    'make_dummy_image',
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
