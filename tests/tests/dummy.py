import io

from django.core.files.base import File
from PIL import Image


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
