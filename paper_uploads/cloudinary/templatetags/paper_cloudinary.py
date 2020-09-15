from functools import partial

from cloudinary.templatetags import cloudinary
from django.template import Library

from ..models.base import CloudinaryFileResource

try:
    import jinja2
except ImportError:
    jinja2 = None

register = Library()


def paper_cloudinary_url(context, source, options_dict=None, **options):
    if isinstance(source, CloudinaryFileResource):
        source = source.get_file().resource
    return cloudinary.cloudinary_url(context, source, options_dict, **options)


@register.simple_tag(takes_context=True, name='paper_cloudinary_url')
def do_paper_cloudinary_url(context, source, options_dict=None, **options):
    return paper_cloudinary_url(context, source, options_dict, **options)


if jinja2 is not None:
    from jinja2 import nodes
    from jinja2.ext import Extension

    class CloudinaryExtension(Extension):
        tags = {'paper_cloudinary_url'}

        def parse(self, parser):
            lineno = parser.stream.current.lineno
            parser.stream.skip(1)

            args = [nodes.ContextReference()]
            kwargs = []
            require_comma = False

            while parser.stream.current.type != 'block_end':
                if require_comma:
                    parser.stream.expect('comma')

                if (
                    parser.stream.current.type == 'name'
                    and parser.stream.look().type == 'assign'
                ):
                    key = parser.stream.current.value
                    parser.stream.skip(2)
                    value = parser.parse_expression()
                    kwargs.append(nodes.Keyword(key, value, lineno=value.lineno))
                else:
                    if kwargs:
                        parser.fail('Invalid argument syntax', parser.stream.current.lineno)
                    args.append(parser.parse_expression())

                require_comma = True

            block_call = self.call_method('_paper_cloudinary_url', args, kwargs)
            call = nodes.MarkSafe(block_call, lineno=lineno)
            return nodes.Output([call], lineno=lineno)

        @staticmethod
        def _paper_cloudinary_url(ctx, *args, caller=None, **kwargs):
            return paper_cloudinary_url(ctx, *args, **kwargs)

    # django-jinja support
    try:
        from django_jinja import library
    except ImportError:
        pass
    else:
        dummy_ctx = {}
        cloudinary_url = partial(paper_cloudinary_url, dummy_ctx)
        library.global_function(name='paper_cloudinary_url')(cloudinary_url)
        library.extension(CloudinaryExtension)
