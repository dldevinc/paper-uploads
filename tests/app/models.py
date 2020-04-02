from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.cloudinary.models import *
from paper_uploads.models import *
from paper_uploads.validators import *
from pilkit import processors


class PageGallery(ImageCollection):
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


class PageFilesGallery(Collection):
    svg = ItemField(SVGItem)
    image = ItemField(ImageItem, options={
        'variations': dict(
            mobile=dict(
                size=(640, 0),
                clip=False
            )
        )
    })
    file = ItemField(FileItem)


class PageCloudinaryGallery(CloudinaryImageCollection):
    pass


class PageCloudinaryFilesGallery(CloudinaryCollection):
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
    cloud_file = CloudinaryFileField(_('file'), blank=True)
    cloud_video = CloudinaryMediaField(_('video'), blank=True)
    cloud_image = CloudinaryImageField(_('image'), blank=True)
    cloud_files = CollectionField(PageCloudinaryFilesGallery, verbose_name=_('file gallery'))
    cloud_gallery = CollectionField(PageCloudinaryGallery, verbose_name=_('image gallery'))

    ext_file = FileField(_('Extension'), blank=True, validators=[
        ExtensionValidator(['jpg', 'jpeg'])
    ], help_text=_('Only `jpg` and `jpeg` extensions allowed'))
    mime_file = FileField(_('Mimetype'), blank=True, validators=[
        MimetypeValidator(['image/jpeg', 'image/png', 'text/plain'])
    ], help_text=_('Only `image/jpeg`, `image/png` and `text/plain` mimetypes allowed'))
    size_file = FileField(_('Size'), blank=True, validators=[
        SizeValidator(128 * 1024)
    ], help_text=_('Up to 128Kb file size allowed'))
    min_image = ImageField(_('Min image'), blank=True, validators=[
        ImageMinSizeValidator(1400, 0)
    ], help_text=_('Minimum width is 1400px'))
    max_image = ImageField(_('Max image'), blank=True, validators=[
        ImageMaxSizeValidator(1024, 640)
    ], help_text=_('Maximum image is 1024x640px'))
    png_gallery = CollectionField(PageGallery, verbose_name=_('PNG gallery'), validators=[
        ExtensionValidator(['png'])
    ])

    order = models.PositiveIntegerField(_('order'), default=0, editable=False)

    class Meta:
        ordering = ['order']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def __str__(self):
        return self.header


class Document(models.Model):
    page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(_('title'), max_length=255)
    image = ImageField(_('simple image'), blank=True)
    files = CollectionField(PageFilesGallery, verbose_name=_('files'))

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')


# =====================
# Коллекции для тестов
# =====================

class DummyCollection(Collection):
    image = ItemField(ImageItem, options={
        'variations': dict(
            mobile=dict(
                size=(640, 0),
                jpeg=dict(
                    quality=88
                )
            )
        )
    })


class DummyCollectionWithMeta(Collection):
    class Meta:
        verbose_name = _('gallery')


class DummyCollectionSubclass(DummyCollection):
    image = ItemField(ImageItem, options={
        'variations': dict(
            preview=dict(
                size=(200, 0),
            )
        )
    })
    svg = ItemField(SVGItem)


class DummyCollectionPostprocessProhibited(Collection):
    image = ItemField(ImageItem, postprocess=False, options={
        'variations': dict(
            mobile=dict(
                size=(640, 0),
                jpeg=dict(
                    quality=88
                ),
                postprocess=dict(
                    webp={
                        'command': 'echo'
                    }
                )
            )
        )
    })


class DummyCollectionOverride(Collection):
    image = ItemField(
        ImageItem,
        postprocess=dict(
            jpeg=False,
            png={
                'command': 'echo'
            },
            webp=False
        ),
        options={
            'variations': dict(
                mobile=dict(
                    size=(640, 0),
                    jpeg=dict(
                        quality=88
                    ),
                    postprocess=dict(
                        webp={
                            'command': 'man'
                        }
                    )
                )
            )
        }
    )
