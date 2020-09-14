import json

from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from ...typing import Limitations


class FileUploaderWidgetMixin:
    validation = None  # type: dict

    def __init__(self, *args, **kwargs):
        self.validation = self.validation or {}
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)  # noqa: F821
        context.update(
            {
                'validation': json.dumps(self.get_validation()),
                'limitations': self.get_limitations(),
            }
        )
        return context

    def get_validation(self):
        model_validation_method = getattr(self.model, 'get_validation', None)  # noqa: F821
        if model_validation_method is not None and callable(model_validation_method):
            model_validation = model_validation_method()
        else:
            model_validation = {}

        return {
            **model_validation,
            **self.validation,
        }

    def get_limitations(self) -> Limitations:
        """
        Список ограничений, накладываемых на загружаемые файлы.
        Используется только для вывода в виде текста.
        """
        limits = []  # type: Limitations
        validation = self.get_validation()
        if not validation:
            return limits

        if 'acceptFiles' in validation:
            accept_files = validation['acceptFiles']
            limits.append(
                (
                    _('Allowed files'),
                    accept_files
                    if isinstance(accept_files, str)
                    else ", ".join(accept_files),
                )
            )
        if 'allowedExtensions' in validation:
            limits.append(
                (_('Allowed extensions'), ", ".join(validation['allowedExtensions']))
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
