from cloudinary.templatetags import cloudinary

from .models.base import CloudinaryFileResource


def paper_cloudinary_url(context, source, options_dict=None, **options):
    if isinstance(source, CloudinaryFileResource):
        source = source.get_file().resource
    return cloudinary.cloudinary_url(context, source, options_dict, **options)
