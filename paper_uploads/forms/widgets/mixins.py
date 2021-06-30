import json

from django.utils.translation import gettext_lazy as _

from ...typing import Limitations
from ...utils import filesizeformat


class FileUploaderWidgetMixin:
    configuration = None  # type: dict

    def __init__(self, *args, **kwargs):
        self.configuration = self.configuration or {}
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)  # noqa: F821
        context.update(
            {
                "configuration": json.dumps(self.get_configuration()),
                "limitations": self.get_limitations(),
            }
        )
        return context

    def get_configuration(self):
        configuration_method = getattr(self.model, "get_configuration", None)  # noqa: F821
        if configuration_method is not None and callable(configuration_method):
            config = configuration_method()
        else:
            config = {}

        config.update(self.configuration)
        return config

    def get_limitations(self) -> Limitations:
        """
        Список ограничений, накладываемых на загружаемые файлы.
        Используется только для вывода в виде текста.
        """
        limits = []  # type: Limitations
        configuration = self.get_configuration()
        if not configuration:
            return limits

        if "acceptFiles" in configuration:
            accept_files = configuration["acceptFiles"]
            limits.append(
                (
                    _("Allowed types"),
                    accept_files
                    if isinstance(accept_files, str)
                    else ", ".join(accept_files),
                )
            )
        if "allowedExtensions" in configuration:
            limits.append(
                (_("Allowed extensions"), ", ".join(configuration["allowedExtensions"]))
            )
        if "sizeLimit" in configuration:
            limits.append(
                (_("Maximum file size"), filesizeformat(configuration["sizeLimit"]))
            )

        min_width = configuration.get("minImageWidth", 0)
        min_height = configuration.get("minImageHeight", 0)
        if min_width:
            if min_height:
                limits.append(
                    (
                        _("Minimum dimensions"),
                        _("%sx%s pixels") % (min_width, min_height),
                    )
                )
            else:
                limits.append((_("Minimum image width"), _("%s pixels") % min_width))
        elif min_height:
            limits.append((_("Minimum image height"), _("%s pixels") % min_height))

        max_width = configuration.get("maxImageWidth", 0)
        max_height = configuration.get("maxImageHeight", 0)
        if max_width:
            if max_height:
                limits.append(
                    (
                        _("Maximum dimensions"),
                        _("%sx%s pixels") % (max_width, max_height),
                    )
                )
            else:
                limits.append((_("Maximum image width"), _("%s pixels") % max_width))
        elif max_height:
            limits.append((_("Maximum image height"), _("%s pixels") % max_height))

        return limits
