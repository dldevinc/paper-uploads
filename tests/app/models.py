from pilkit import processors
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import gallery
from paper_uploads.models.fields import FileField, ImageField, CollectionField, CollectionItemTypeField


class PageGallery(gallery.ImageCollection):
    VARIATIONS = dict(
        wide_raw=dict(
            size=(1600, 0),
            clip=False,
            jpeg=dict(
                postprocess=None
            )
        ),
        wide=dict(
            size=(1600, 0),
            clip=False,
        ),
        desktop=dict(
            size=(1280, 0),
            clip=False,
        ),
        tablet=dict(
            size=(960, 0),
            clip=False,
        ),
        mobile=dict(
            size=(640, 0),
        )
    )


class PageFilesGallery(gallery.Gallery):
    svg = CollectionItemTypeField(gallery.SVGItem)
    image = CollectionItemTypeField(gallery.ImageItem)
    file = CollectionItemTypeField(gallery.FileItem)


class Page(models.Model):
    header = models.CharField(_('header'), max_length=255)
    file = FileField(_('simple file'), blank=True)
    image = ImageField(_('simple image'), blank=True)
    image_ext = ImageField(_('image with variations'), blank=True,
        variations=dict(
            desktop=dict(
                size=(1600, 0),
                clip=False,
                format='jpeg',
                jpeg=dict(
                    quality=92,
                ),
                postprocessors=[
                    processors.ColorOverlay('#FF0000'),
                ],
            ),
            tablet=dict(
                size=(1024, 0),
                clip=False,
            ),
            admin=dict(
                size=(320, 0),
                clip=False,
            )
        )
    )
    files = CollectionField(PageFilesGallery, verbose_name=_('file gallery'))
    gallery = CollectionField(PageGallery, verbose_name=_('image gallery'))
    order = models.PositiveIntegerField(_('order'), default=0, editable=False)

    class Meta:
        ordering = ['order']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def __str__(self):
        return self.header


class Document(models.Model):
    title = models.CharField(_('title'), max_length=255)
    image = ImageField(_('simple image'), blank=True)
    files = CollectionField(PageFilesGallery, verbose_name=_('files'))

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
