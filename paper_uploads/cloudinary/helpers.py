from cloudinary.templatetags import cloudinary

from .models.base import CloudinaryFileFieldResourceMixin


def paper_cloudinary_url(context, source, options_dict=None, **options):
    if isinstance(source, CloudinaryFileFieldResourceMixin):
        source = source.get_file().resource
    return cloudinary.cloudinary_url(context, source, options_dict, **options)
