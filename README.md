# paper-uploads

![](http://joxi.net/gmvnGZBtqKOOjm.png)

Предоставляет поля для асинхронной загрузки файлов. Включает
три класса полей для моделей: 
* `paper_uploads.models.fields.FileField` для загрузки одного файла.
* `paper_uploads.models.fields.ImageField` для загрузки одной картинки 
(с возможностью нарезки на дополнительные вариации)
* `paper_uploads.models.fields.CollectionField` для загрузки множества 
файлов (не обязательно картинок). Для загружаемых картинок есть 
возможность нарезки на дополнительные вариации.

## Requirements
* Python (3.5, 3.6, 3.7)
* Django (2.1, 2.2)
* [paper-admin](https://github.com/dldevinc/paper-admin)
* [variations](https://github.com/dldevinc/variations)

## Features
* Каждый файл представлен своей моделью, что позволяет
хранить метаданные. Например alt и title для изображения.
* Загрузка файлов происходит асинхронно.
* Поля для хранения файлов являются производными
от OneToOneField и не используют <input type="file">. Благодаря
этому, при ошибках валидации формы, не нужно прикреплять файлы 
повторно.
* Загруженные картинки можно нарезать на множество вариаций.
Каждая вариация гибко настраивается. Можно указать размеры, 
качество сжатия, формат, добавить дополнительные 
[pilkit](https://github.com/matthewwithanm/pilkit)-процессоры, 
распознавание лиц и другое. См. 
[variations](https://github.com/dldevinc/variations).
* Интеграция с [django-rq](https://github.com/rq/django-rq)
для отложенной нарезки картинок на вариации.
* Возможность постобработки вариаций консольными утилитами. 
Такими как `mozjpeg` и `pngquant`.

## Installation
```python
INSTALLED_APPS = [
    # ...
    'paper_uploads',
    # ...
]

PAPER_UPLOADS = {
    'RQ_ENABLED': True,
    'POSTPROCESS': {
        'JPEG': {
            'COMMAND': 'jpeg-recompress',
            'ARGUMENTS': '--quality high --method smallfry {file} {file}',
        },
        'PNG': {
            'COMMAND': 'pngquant',
            'ARGUMENTS': '--force --skip-if-larger --output {file} {file}'
        },
        'SVG': {
            'COMMAND': 'svgo',
            'ARGUMENTS': '--precision=4 {file}',
        },   
    }
}
```

## FileField
Поле для загрузки файла. Никаких ограничений на загружаемые файлы 
по-умолчанию нет. Но их можно добавить с помощью [валидаторов](#Validation).

```python
from django.db import models
from paper_uploads.models.fields import FileField
from paper_uploads.validators import SizeValidator


class Page(models.Model):
    file = FileField(_('file'), blank=True, validators=[
        SizeValidator(10*1024*1024)    # limit to 10Mb    
    ])
```

## ImageField
Поле для загрузки изображений. Поддерживает нарезку на неограниченное 
количество вариаций (опционально). Настройки вариаций идентичны 
настройкам модуля [variations](https://github.com/dldevinc/variations).

В любом случае, исходное изображение сохраняется. При добавлении
новых вариаций или изменении существующих, можно заново произвести
нарезку с помощью команды [recreate_variations](#recreate_variations)

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

## CollectionField
Для создания галереи необходимо создать класс модели галереи, 
унаследованый от `Gallery` или `ImageGallery`.

Галерея может включать элементы любого вида, который можно 
описать с помощью модели, унаследованной от `GalleryItemBase`. 
Перечень допустимых классов элементов галереи задается
с помощью `GalleryItemTypeField`. Синтаксис подключения 
подобен добавлению поля `ForeignKey` к модели.

"Из коробки" доступны следующие классы элементов галереи:
* `ImageItem` - изображение с вариациями.
* `FileItem` - любой файл.
* `SVGItem` - для хранения svg-файлов. Аналогичен `FileItem`, но в превью админки показывается картинка.

```python
from paper_uploads.models import gallery
from paper_uploads.models.fields import CollectionItemTypeField


class PageFiles(gallery.Gallery):
    svg = CollectionItemTypeField(gallery.SVGItem)
    image = CollectionItemTypeField(gallery.ImageItem)
    file = CollectionItemTypeField(gallery.FileItem)
```

Порядок подключения классов имеет значение: при загрузке
файла через админку, его класс определется первым классом,
чей метод `check_file` вернет `True`. 

Менять имена полей `GalleryItemTypeField` нельзя, т.к при 
добавлении нового элемента это имя заносится в БД.

---

Для галерей, предназначенных исключительно для изображений, 
"из коробки" доступна модель для наследования `ImageGallery`,
с предустановленным фильтром mimetype на этапе выбора файла.

```python
from django.db import models
from paper_uploads.models import gallery
from paper_uploads.models.fields import CollectionField, GalleryItemTypeField


class PageFiles(gallery.Gallery):
    svg = GalleryItemTypeField(gallery.SVGItem)
    file = GalleryItemTypeField(gallery.FileItem)


class PageImages(gallery.ImageCollection):
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
    files = CollectionField(PageFiles, verbose_name=_('files'))
    images = CollectionField(PageImages, verbose_name=_('images'))
```

---

Наследование от `Gallery` на самом деле создает
[proxy-модель](https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models),
чтобы не плодить множество однотипных таблиц в БД. Благодаря 
переопределенному менеджеру `objects` в классе `Gallery`, запросы 
через этот менеджер будут затрагивать только галереи того же класса, 
от имени которого вызываются.

```python
# Вернет только галереи класса MyGallery
MyGallery.objects.all()

# Вернет абсолютно все галереи, всех классов
MyGallery._base_manager.all()
```  

## Programmatically upload files
```python
from django.core.files import File
from paper_uploads.models import UploadedFile, ImageItem

# file / image
with open('file.doc', 'rb') as fp:
    file = UploadedFile(
        file=File(fp, name='file.doc'),
    )
    file.save()

# gallery
gallery = PageGallery.objects.create()
with open('image.jpg', 'rb') as fp:
    item = ImageItem(
        file=File(fp, name='image.jpg'),
    )
    item.attach_to(gallery)
    item.save()
```

## Appearance
Модели файлов проксируют некоторые свойства файла на уровень
модели:
* `url`
* `path`
* `open`
* `read`
* `close`
* `closed`

Таким образом, вместо `Page.image.file.url` можно 
использовать `Page.image.url`.

## Management Commands
#### check_uploads
Проверяет все записи в БД на целостность. Обнаруживает 
некорректные ссылки на модель-владельца файла 
и отсутствие файлов вариаций.

При указании ключа `--fix-missing` все отстутствующие 
вариации будут перенарезаны из исходников.

```python
python3 manage.py check_uploads --fix-missing
```

#### clean_uploads
Находит мусорные записи в БД. Например те, у которых 
нет владельца, и предлагает их удалить.

Так как при заполнении формы в админке, владелец
устанавливается в последнюю очередь, при очистке
могут быть удалены только что загруженные кем-то файлы.
Поэтому файлы, созданные менее, чем 30 минут назад
игнорируются. Поменять длину безопасного интервала 
(в минутах) можно через ключ `--since`.  

```python
python3 manage.py clean_uploads --since=10
```

#### recreate_variations
Перенарезает вариации для указанных моделей / полей.
Можно указать:
* модель галереи. Будут перенарезаны вариации для всех
элементов галереи.
* поле модели. В этом случае будут перенарезаны все вариации
этого поля для всех экзепляров указанной модели.

Если нужно перенарезать не все доступные вариации, а только
определённые, то их можно перечислить в параметре `--variations`.

```python
python3 manage.py recreate_variations 'page.PageGallery' --variations big small
python3 manage.py recreate_variations 'page.Page' --field=image 
```

## Validation
* `SizeLimitValidator` - устанавливает максимально допустимый
размер загружаемого файла в байтах.
* `ImageMinSizeValidator` - устанавливает минимальный размер загружаемых изображений.
* `ImageMaxSizeValidator` - устанавливает максимальный размер загружаемых изображений.

```python
from django.db import models
from paper_uploads.models import Gallery, FileItem
from paper_uploads.models.fields import ImageField, CollectionItemTypeField 
from paper_uploads.validators import SizeValidator, ImageMaxSizeValidator

class Page(models.Model):
    image = ImageField(_('image'), blank=True, validators=[
        SizeValidator(10 * 1024 * 1024),   # max 10Mb
        ImageMaxSizeValidator(800, 800)     # max dimensions 800x800
    ])


class PageGallery(Gallery):
    file = CollectionItemTypeField(FileItem, validators=[
        SizeValidator(10 * 1024 * 1024), 
    ])
```

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
| POSTPROCESS | Словарь, задающий команды, запускаемые после загрузки файла. Для каждого формата своя команда. |
