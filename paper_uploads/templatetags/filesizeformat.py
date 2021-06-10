from django.template import library
from ..utils import filesizeformat

register = library.Library()


@register.filter
@register.filter(name="filesizeformat", is_safe=True)
def do_filesizeformat(bytes_):
    return filesizeformat(bytes_)
