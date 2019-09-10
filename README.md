# paper-uploads

![](http://joxi.net/gmvnGZBtqKOOjm.png)

Предоставляет поля для асинхронной загрузки файлов. Включает
три класса полей для моделей: 
* `paper_uploads.models.fields.FileField` для загрузки одного файла.
* `paper_uploads.models.fields.ImageField` для загрузки одной картинки (с возможностью
нарезки на дополнительные вариации)
* `paper_uploads.models.fields.GalleryField` для загрузки множества файлов (не обязательно картинок).
Для загружаемых картинок есть возможность нарезки на 
дополнительные вариации.

## Requirements
* Python (3.5, 3.6, 3.7)
* Django (2.1, 2.2)
* [paper-admin](https://github.com/dldevinc/paper-admin)
* [variations](https://github.com/dldevinc/variations)

## Features
* По-умолчанию, если при сохранении формы были ошибки
валидации, то все выбранные на форме файлы сбрасывались.
При асинхронной загрузке файлов такого больше не будет.
* Загруженные картинки можно нарезать на множество вариаций.
Каждая вариация гибко настраивается. Можно указать качество сжатия,
размеры, добавить дополнительные 
[pilkit](https://github.com/matthewwithanm/pilkit)-процессоры, 
распознавание лиц и другое.
* Для каждого файла можно указать метаданные. 
Для файлов - имя файла и отображаемое имя.
Для картинок - имя файла, alt и title.
* Интеграция с [django-rq](https://github.com/rq/django-rq)
для отложенной нарезки картинок на вариации.
* Возможность постобработки вариаций такими 
утилитами как `mozjpeg` и `pngquant`.

## Installation
```python
INSTALLED_APPS = [
    # ...
    'paper_uploads',
    # ...
]

PAPER_UPLOADS = {
    'STORAGE': 'django.core.files.storage.FileSystemStorage',
    'RQ_ENABLED': True,
    'POSTPROCESS_JPEG': {
        'COMMAND': 'cjpeg',
        'ARGUMENTS': '-copy none -progressive -optimize -outfile {file} {file}'
    },
    'POSTPROCESS_PNG': {
        'COMMAND': 'pngquant',
        'ARGUMENTS': '--force --skip-if-larger --speed 2 --output {file} {file}'
    }
}
```

## FileField
```python
from django.db import models
from paper_uploads.models.fields import FileField


class Page(models.Model):
    file = FileField(_('simple file'), blank=True)
```

## ImageField
Натсройки вариаций идентичны настройкам модуля [variations](https://github.com/dldevinc/variations).
```python
from pilkit import processors
from django.db import models
from paper_uploads.models.fields import ImageField


class Page(models.Model):
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
```

## GalleryField
Для создания галереи необходимо создать класс, унаследованый 
от `Gallery`. 

Галерея может включать элементы практически 
любого вида (изображение с вариациями, SVG-файл, простой файл).
Каждый такой тип должен описывается моделью, унаследованной от 
`GalleryItemBase`.

"Из коробки" доступны  следующие виды элементов галереи:
* `GalleryImageItem` - изображение с вариациями.
* `GalleryFileItem` - любой файл.
* `GallerySVGItem` - для хранения svg-файлов. Аналогичен `GalleryFileItem`, но в превью админки показывается картинка.

Для галерей, предназначенных исключительно для изображений (не SVG)
"из коробки" доступна модель для наследования `ImageGallery`, 
с предустановленным контролем mimetype на этапе выбора файла.

```python
from django.db import models
from paper_uploads.models.fields import GalleryField
from paper_uploads.models import (
    Gallery, ImageGallery, GalleryFileItem, GallerySVGItem
)


class PageFiles(Gallery):
    ALLOWED_ITEM_TYPES = {
        'file': GalleryFileItem,
        'svg': GallerySVGItem,
    }


class PageImages(ImageGallery):
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


class Page(models.Model):
    files = GalleryField(PageFiles, verbose_name=_('files'))
    images = GalleryField(PageImages, verbose_name=_('images'))
```

## Programmatically upload files
```python
from django.core.files import File
from paper_uploads.models import UploadedFile, GalleryImageItem

# file / image
with open('file.doc', 'rb') as fp:
    file = UploadedFile(
        file=File(fp, name='file.doc'),
    )
    file.full_clean()   # optional validation
    file.save()

# gallery
gallery = PageGallery.objects.create()
with open('image.jpg', 'rb') as fp:
    item = GalleryImageItem(
        file=File(fp, name='image.jpg'),
    )
    item.attach_to(gallery)
    item.full_clean()   # optional validation
    item.save()
```

## Appearance
Модели файлов проксируют некоторые свойства файла на уровень модели:
* `url`
* `path`
* `open`
* `read`
* `close`
* `closed`

Таким образом, вместо `Page.image.file.url` можно использовать `Article.image.url`.

## Settings
Все настройки указываются в словаре `PAPER_UPLOADS`.

| Option | Description |
| --- | --- |
| STORAGE | Путь к классу хранилища Django |
| STORAGE_OPTIONS | Параметры инициализации хранилища |
| FILES_UPLOAD_TO | Путь к папке, в которую загружаются файлы из FileField. По умолчанию, `files/%Y-%m-%d` |
| IMAGES_UPLOAD_TO | Путь к папке, в которую загружаются файлы ImageField. По умолчанию, `images/%Y-%m-%d` |
| GALLERY_FILES_UPLOAD_TO | Путь к папке, в которую загружаются файлы галереи. По умолчанию, `gallery/files/%Y-%m-%d` |
| GALLERY_IMAGES_UPLOAD_TO | Путь к папке, в которую загружаются картинки галереи. По умолчанию, `gallery/images/%Y-%m-%d` |
| GALLERY_ITEM_PREVIEW_WIDTH | Ширина превью элемента галереи в виджете админки. По-умолчанию, `144` |
| GALLERY_ITEM_PREVIEW_HEIGHT | Высота превью элемента галереи в виджете админки. По-умолчанию, `108` |
| GALLERY_IMAGE_ITEM_PREVIEW_VARIATIONS | Вариации для превью картинок галереи в виджете админки. |
| RQ_ENABLED | Включает нарезку картинок на вариации через отложенные задачи. Требует наличие установленного пакета [django-rq](https://github.com/rq/django-rq) |
| RQ_QUEUE_NAME | Название очереди, в которую помещаются задачи по нарезке картинок. По-умолчанию, `default` |
| POSTPROCESS_JPEG, POSTPROCESS_PNG, POSTPROCESS_GIF | Словари, задающие команду, запускаемую после нарезки вариации. Для каждого формата своя команда. Путь к исполняемому файлу передается в ключе COMMAND, а её аргументы в ключе ARGUMENTS.  |
