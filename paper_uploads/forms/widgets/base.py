import json
from typing import List, Tuple

from django.contrib.contenttypes.models import ContentType
from django.forms import widgets
from django.template.defaultfilters import filesizeformat
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _


class FileWidgetBase(widgets.Widget):
    owner_app_label = None
    owner_model_name = None
    owner_fieldname = None
    validation = None

    def __init__(self, *args, **kwargs):
        self.validation = self.validation or {}
        super().__init__(*args, **kwargs)

    @cached_property
    def model(self):
        return self.choices.queryset.model

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update(
            {
                'content_type': ContentType.objects.get_for_model(
                    self.model, for_concrete_model=False
                ),
                'owner_app_label': self.owner_app_label,
                'owner_model_name': self.owner_model_name,
                'owner_fieldname': self.owner_fieldname,
                'validation': json.dumps(self.get_validation()),
                'validation_lines': self.get_validation_lines(),
                'instance': self.get_instance(value) if value else None,
            }
        )
        return context

    def get_instance(self, value):
        return self.model._base_manager.get(pk=value)

    def get_validation(self):
        model_validation_method = getattr(self.model, 'get_validation', None)
        if model_validation_method is not None and callable(model_validation_method):
            model_validation = model_validation_method()
        else:
            model_validation = {}

        return {
            **model_validation,
            **self.validation,
        }

    def get_validation_lines(self) -> List[Tuple[str, str]]:
        """
        Получение ограничений на загружаемые файлы в виде текста
        """
        limits = []  # type: List[Tuple[str, str]]
        validation = self.get_validation()
        if not validation:
            return limits

        if 'allowedExtensions' in validation:
            limits.append(
                (_('Allowed extensions'), ", ".join(validation['allowedExtensions']))
            )
        if 'acceptFiles' in validation:
            accept_files = validation['acceptFiles']
            limits.append(
                (
                    _('Allowed MIME types'),
                    accept_files
                    if isinstance(accept_files, str)
                    else ", ".join(accept_files),
                )
            )
        if 'sizeLimit' in validation:
            limits.append(
                (_('Maximum file size'), filesizeformat(validation['sizeLimit']))
            )

        min_width = validation.get('minImageWidth', 0)
        min_height = validation.get('minImageHeight', 0)
        if min_width:
            if min_height:
                limits.append(
                    (
                        _('Minimum image size'),
                        _('%sx%s pixels') % (min_width, min_height),
                    )
                )
            else:
                limits.append((_('Minimum image width'), _('%s pixels') % min_width))
        elif min_height:
            limits.append((_('Minimum image height'), _('%s pixels') % min_height))

        max_width = validation.get('maxImageWidth', 0)
        max_height = validation.get('maxImageHeight', 0)
        if max_width:
            if max_height:
                limits.append(
                    (
                        _('Maximum image size'),
                        _('%sx%s pixels') % (max_width, max_height),
                    )
                )
            else:
                limits.append((_('Maximum image width'), _('%s pixels') % max_width))
        elif max_height:
            limits.append((_('Maximum image height'), _('%s pixels') % max_height))
        return limits
