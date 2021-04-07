from functools import partial

from django.template import Library
from jinja2_simple_tags import StandaloneTag

from ..helpers import paper_cloudinary_url

try:
    import jinja2
except ImportError:
    jinja2 = None

register = Library()


@register.simple_tag(takes_context=True, name="paper_cloudinary_url")
def do_paper_cloudinary_url(context, source, options_dict=None, **options):
    return paper_cloudinary_url(context, source, options_dict, **options)


if jinja2 is not None:
    class CloudinaryExtension(StandaloneTag):
        tags = {"paper_cloudinary_url"}

        def render(self, *args, **kwargs):
            return paper_cloudinary_url(self.context, *args, **kwargs)

    # django-jinja support
    try:
        from django_jinja import library
    except ImportError:
        pass
    else:
        dummy_ctx = {}
        cloudinary_url = partial(paper_cloudinary_url, dummy_ctx)
        library.global_function(name="paper_cloudinary_url")(cloudinary_url)
        library.extension(CloudinaryExtension)
