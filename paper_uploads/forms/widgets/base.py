import json
from django.forms import widgets
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.contrib.contenttypes.models import ContentType


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
        context.update({
            'content_type': ContentType.objects.get_for_model(self.model, for_concrete_model=False),
            'owner_app_label': self.owner_app_label,
            'owner_model_name': self.owner_model_name,
            'owner_fieldname': self.owner_fieldname,
            'validation': json.dumps(self.get_validation()),
            'validation_lines': self.get_validation_lines(),
            'instance': self.get_instance(value) if value else None,
        })
        return context

    def get_instance(self, value):
        return self.model._base_manager.get(pk=value)

    def get_validation(self):
        return {
            **self.model.get_validation(),
            **self.validation,
        }

    def get_validation_lines(self):
        """
        Получение ограничений на загружаемые файлы в виде текста
        """
        limits = []
        validation = self.get_validation()
        if not validation:
            return limits

        if 'allowedExtensions' in validation:
            limits.append((
                _('Allowed extensions'),
                ", ".join(validation['allowedExtensions'])
            ))
        if 'acceptFiles' in validation:
            acceptFiles = validation['acceptFiles']
            limits.append((
                _('Allowed MIME types'),
                acceptFiles if isinstance(acceptFiles, str) else ", ".join(acceptFiles)
            ))
        if 'sizeLimit' in validation:
            limits.append((
                _('Maximum file size'),
                filesizeformat(validation['sizeLimit'])
            ))

        minWidth = validation.get('minImageWidth', 0)
        minHeight = validation.get('minImageHeight', 0)
        if minWidth:
            if minHeight:
                limits.append((
                    _('Minimum image size'),
                    _('%sx%s pixels') % (minWidth, minHeight)
                ))
            else:
                limits.append((
                    _('Minimum image width'),
                    _('%s pixels') % minWidth
                ))
        elif minHeight:
            limits.append((
                _('Minimum image height'),
                _('%s pixels') % minHeight
            ))

        maxWidth = validation.get('maxImageWidth', 0)
        maxHeight = validation.get('maxImageHeight', 0)
        if maxWidth:
            if maxHeight:
                limits.append((
                    _('Maximum image size'),
                    _('%sx%s pixels') % (maxWidth, maxHeight)
                ))
            else:
                limits.append((
                    _('Maximum image width'),
                    _('%s pixels') % maxWidth
                ))
        elif maxHeight:
            limits.append((
                _('Maximum image height'),
                _('%s pixels') % maxHeight
            ))
        return limits
