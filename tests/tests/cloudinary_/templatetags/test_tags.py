from django.template import engines

from paper_uploads.cloudinary.models import CloudinaryImage

from ...dummy import *

DJANGO_TEMPLATE = '''
    {% load paper_cloudinary %}
    <img src="{% paper_cloudinary_url image width=320 crop="fill" %}">
'''

JINJA2_TEMPLATE = '''
    <img src="{% paper_cloudinary_url image, width=320, crop="fill" %}">
'''

JINJA2_FUNC_TEMPLATE = '''
    <img src="{{ paper_cloudinary_url(image, width=320, crop="fill") }}">
'''


class TestTemplateTags:
    @classmethod
    def init_class(cls, storage):
        storage.resource = CloudinaryImage(
            owner_app_label='app',
            owner_model_name='cloudinaryimageexample',
            owner_fieldname='image'
        )
        with open(NATURE_FILEPATH, 'rb') as fp:
            storage.resource.attach_file(fp)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_django(self, storage):
        engine = engines['django']
        template = engine.from_string(DJANGO_TEMPLATE)
        html = template.render({
            'image': storage.resource
        }).strip()
        assert html.startswith('<img src="https://res.cloudinary.com/')
        assert '/c_fill,w_320/' in html
        assert '/Nature_Tree' in html

    def test_jinja2(self, storage):
        engine = engines['jinja2']
        template = engine.from_string(JINJA2_TEMPLATE)
        html = template.render({
            'image': storage.resource
        }).strip()
        assert html.startswith('<img src="https://res.cloudinary.com/')
        assert '/c_fill,w_320/' in html
        assert '/Nature_Tree' in html

    def test_jinja2_func(self, storage):
        engine = engines['jinja2']
        template = engine.from_string(JINJA2_FUNC_TEMPLATE)
        html = template.render({
            'image': storage.resource
        }).strip()
        assert html.startswith('<img src="https://res.cloudinary.com/')
        assert '/c_fill,w_320/' in html
        assert '/Nature_Tree' in html
