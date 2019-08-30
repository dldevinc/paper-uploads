from pilkit import processors
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import Gallery, ImageGallery
from paper_uploads.models.fields import FileField, ImageField, GalleryField


class PageGallery(ImageGallery):
    VARIATIONS = dict(
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


class PageFilesGallery(Gallery):
    pass


class Page(models.Model):
    header = models.CharField(_('header'), max_length=255)
    file = FileField(_('simple file'), blank=True)
    image = ImageField(_('simple image'), blank=True)
    image_ext = ImageField(_('image with variations'), blank=True,
        variations=dict(
            desktop=dict(
                size=(1600, 0),
                clip=False,
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
    files = GalleryField(PageFilesGallery, verbose_name=_('file gallery'))
    gallery = GalleryField(PageGallery, verbose_name=_('image gallery'))
    order = models.PositiveIntegerField(_('order'), default=0, editable=False)

    class Meta:
        ordering = ['order']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def __str__(self):
        return self.header
