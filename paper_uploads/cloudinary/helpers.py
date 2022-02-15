from cloudinary.templatetags import cloudinary

from .models.base import CloudinaryFileFieldResource


def paper_cloudinary_url(context, source, options_dict=None, **options):
    if isinstance(source, CloudinaryFileFieldResource):
        source = source.get_file().resource
    return cloudinary.cloudinary_url(context, source, options_dict, **options)
