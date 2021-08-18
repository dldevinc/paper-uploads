import json
from django.template import library
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import _json_script_escapes
from django.utils.safestring import mark_safe

register = library.Library()


@register.filter
@register.filter(name="json", is_safe=True)
def do_json(value):
    data = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
    return mark_safe(data)
