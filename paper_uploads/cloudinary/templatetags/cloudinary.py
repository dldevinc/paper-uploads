from functools import partial

from cloudinary.templatetags.cloudinary import cloudinary_url

from ..models.base import CloudinaryFileResource

try:
    import jinja2
except ImportError:
    jinja2 = None


if jinja2 is not None:
    from jinja2.ext import Extension, nodes

    def paper_cloudinary(func):
        """
        Декоратор для функций модуля cloudinary, позволяющий передавать в качестве
        source экземпляры CloudinaryContainerMixin.
        """

        def inner(ctx, source, *args, **kwargs):
            if isinstance(source, CloudinaryFileResource):
                source = source.file
            return func(ctx, source, *args, **kwargs)

        return inner

    class CloudinaryExtension(Extension):
        tags = {'cloudinary_url'}

        def parse(self, parser):
            lineno = next(parser.stream).lineno
            args = [nodes.ContextReference()]
            kwargs = []
            while parser.stream.current.type != 'block_end':
                if (
                    parser.stream.current.type == 'name'
                    and parser.stream.look().type == 'assign'
                ):
                    name = parser.stream.expect('name')
                    parser.stream.expect('assign')
                    value = parser.parse_expression()
                    kwargs.append(nodes.Keyword(name.value, value, lineno=value.lineno))
                else:
                    args.append(parser.parse_expression())
            return nodes.CallBlock(
                self.call_method('_cloudinary_url', args, kwargs), [], [], []
            ).set_lineno(lineno)

        @staticmethod
        def _cloudinary_url(ctx, *args, caller=None, **kwargs):
            return paper_cloudinary(cloudinary_url)(ctx, *args, **kwargs)

    # django-jinja support
    try:
        from django_jinja import library
    except ImportError:
        pass
    else:
        dummy_ctx = {}
        cloudinary_url = partial(paper_cloudinary(cloudinary_url), dummy_ctx)
        library.global_function(name='cloudinary_url')(cloudinary_url)

        library.extension(CloudinaryExtension)
