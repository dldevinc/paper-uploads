# paper-uploads
Асинхронная загрузка файлов для административного интерфейса Django.

[![PyPI](https://img.shields.io/pypi/v/paper-uploads.svg)](https://pypi.org/project/paper-uploads/)
[![Build Status](https://travis-ci.org/dldevinc/paper-uploads.svg?branch=master)](https://travis-ci.org/dldevinc/paper-uploads)

![](http://joxi.net/gmvnGZBtqKOOjm.png)

## Requirements
* Python 3.6+
* Django 2.1+
* [paper-admin][paper-admin]
* [variations][variations]

## Features
* Каждый файл представлен своей моделью, что позволяет
хранить вместе с изображением дополнительные данные. 
Например, `alt` и `title`.
* Загрузка файлов происходит асинхронно и начинается сразу, 
при выборе файла в интерфейсе администратора.
* Поля модели, ссылающиеся на файлы, являются производными
от `OneToOneField` и не используют `<input type="file">`. 
Благодаря этому, при ошибках валидации прикрепленные файлы 
не сбрасываются.
* Загруженные картинки можно нарезать на множество вариаций.
Каждая вариация гибко настраивается. Можно указать размеры,
качество сжатия, формат, добавить дополнительные
[pilkit][pilkit]-процессоры, распознавание лиц и другое.
См. [variations][variations].
* Совместим с [django-storages][django-storages].
* Опциональная интеграция с [django-rq][django-rq]
для отложенной нарезки картинок на вариации.
* Внутренний подмодуль `paper_uploads.cloudinary` предоставляет
поля и классы, реализующие хранение файлов в облаке 
[Cloudinary][pycloudinary].
* Возможность создавать коллекции файлов. В частности, галерей
изображений с возможностью сортировки элементов.

## Installation

Install `paper-uploads`:
```shell script
pip install paper-uploads[full]
```

Add `paper_uploads` to `INSTALLED_APPS` in `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'paper_uploads',
    # ...
]
```

Configure `paper-uploads` in django's `settings.py`:
```python
PAPER_UPLOADS = {
    'VARIATION_DEFAULTS': {
        'jpeg': dict(
            quality=80,
            progressive=True,
        ),
        'webp': dict(
            quality=75,
        )
    }
}
```

## FileField
Поле для загрузки файла.

На загружаемые файлы можно наложить ограничения с помощью
[валидаторов](#validators).
```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *
from paper_uploads.validators import *


class Page(models.Model):
    report = FileField(_('file'), blank=True, validators=[
        SizeValidator(10*1024*1024)    # up to 10Mb
    ])
```

При загрузке файла создается экземпляр модели `UploadedFile`.

### UploadedFile

Модель, представляющая загруженный файл.

Поля и свойства модели:
* `file` - ссылка на файл, хранящийся в Django-хранилище.
* `basename` - имя файла без пути, суффикса и расширения. 
Пример: `my_document`.
* `extension` - расширение файла в нижнем регистре. Пример: `doc`.
* `name` - полное имя файла. Пример: `files/my_document_19sc2Kj.pdf`.
* `display_name`- удобочитаемое название файла для вывода на сайте.
Пример: `Отчёт за 2019 год`.
* `size` - размер файла в байтах.
* `checksum` - контрольная сумма файла. Используется для отслеживания
изменения файла.
* `created_at` - дата создания экземпляра модели.
* `modified_at` - дата изменения модели.
* `uploaded_at` - дата загрузки файла.

Для упрощения работы с файлами, некоторые методы и свойства
стандартного класса `FieldFile` проксированы на уровень модели:
`UploadedFile`:
* `open`
* `close`
* `closed`
* `read`
* `seek`
* `tell`
* `readable`
* `writable`
* `seekable`
* `url`
* `path`
* `chunks`

Таким образом, вместо `Page.report.file.url` можно использовать
`Page.report.url`.

## ImageField
Поле для загрузки изображений.

Во многом аналогично [FileField](#FileField). Может хранить ссылку 
как на единственное изображение (подобно стандартному полю 
`ImageField`), так и на семейство вариаций одного изображения,
созданных из исходного с помощью библиотеки [variations][variations]. 

```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *


class Page(models.Model):
    image = ImageField(_('single image'), blank=True)
    image_set = ImageField(_('image with variations'),
        blank=True,
        variations=dict(
            desktop=dict(
                size=(1600, 0),
                clip=False,
                jpeg=dict(
                    quality=80,
                    progressive=True
                ),
            ),
            tablet=dict(
                size=(1024, 0),
                clip=False,
                jpeg=dict(
                    quality=75,
                ),
            ),
            mobile=dict(
                size=(640, 0),
                clip=False,
            )
        )
    )
```

При загрузке изображения создается экземпляр модели `UploadedImage`.

### UploadedImage

Модель, представляющая загруженное изображение.

Поля и свойства модели:
* `file` - ссылка на файл, хранящийся в Django-хранилище.
* `basename` - имя файла без пути, суффикса и расширения. 
Пример: `my_image`.
* `extension` - расширение файла в нижнем регистре. Пример: `jpg`.
* `name` - полное имя файла. Пример: `images/my_image_19sc2Kj.jpg`.
* `size` - размер файла в байтах.
* `title` - текст атрибута `title` для тэга `<img>`.
* `description` - текст атрибута `alt` для тэга `<img>`.
* `width` - ширина исходного изображения в пикселях.
* `height` - высота исходного изображения в пикселях.
* `checksum` - контрольная сумма файла. Используется для отслеживания
изменения файла.
* `created_at` - дата создания экземпляра модели.
* `modified_at` - дата изменения модели.
* `uploaded_at` - дата загрузки файла.

По аналогии с `FileField`, модель `UploadedImage` проксирует
методы и свойства стандартного класса `FieldFile`.

К вариациям можно обращаться прямо из экземпляра `UploadedImage`:
```python
page.image_set.desktop.url
```

По умолчанию, нарезка изображения на вариации происходит
при его загрузке. Можно перенести процесс нарезки в отложенную
задачу `django-rq`, установив значение `RQ_ENABLED` в `True`
в настройках модуля.

```python
# settings.py
PAPER_UPLOADS = {
    # ...
    'RQ_ENABLED': True,
    'RQ_QUEUE_NAME': 'default'
}
```

## Collections
Коллекция — это модель, группирующая экземпляры других моделей
(элементов коллекции). В частности, с помощью коллекции можно
создать фото-галерею или список файлов.

Для создания коллекции необходимо создать класс, унаследованный
от `Collection` и объявить модели элементов, которые могут входить
в коллекцию. Синтаксис объявления элементов подобен добавлению полей:

```python
from paper_uploads.models import *


class PageFiles(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)
```

Псевдо-поле `CollectionItem` подключает к коллекции модель
элемента под заданным именем. Это имя записывается в БД при добавлении
элемента к коллекции и позволяет фильтровать элементы по их типу.
При изменении имен псевдо-полей или при удалении класса элемента
из существующих коллекций, разработчик должен самостоятельно
обеспечить согласованное состояние БД.

В примере выше, коллекция `PageFiles` может содержать элементы трех
классов: `FileItem`, `ImageItem` и `SVGItem`. У элементов коллекции
с типом `FileItem` в поле `item_type` будет записано значение `file`,
у элементов `ImageItem` - `image` и т.п.

Порядок подключения классов элементов к коллекции имеет значение:
первый класс, чей метод `file_supported()` вернет `True`,
определит модель загружаемого файла. Поэтому `FileItem` должен
указываться последним, т.к. он принимает любые файлы.

Вместе с моделью элемента, в поле `CollectionItem` можно указать
[валидаторы](#Validators) и дополнительные параметры
(в словаре `options`), которые могут быть использованы для
более детальной настройки элемента коллекции.

Полученную коллекцию можно подключать к моделям с помощью
`CollectionField`:

```python
from django.db import models
from paper_uploads.models import *


class PageFiles(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)


class Page(models.Model):
    files = CollectionField(PageFiles)
```

---

В состав библиотеки входят следующие классы элементов:
* `FileItem`. Может хранить любой файл. Из-за этого при
подключении к коллекции этот тип должен быть подключен последним.
* `SVGItem`. Функционально иденичен `FileItem`, но в админке вместо
абстрактной иконки показывается само SVG-изображение.
* `ImageItem`. Для хранения изображения с возможностью нарезки
на вариации.

Вариации для изображений коллекции можно указать двумя способами:
1) в члене класса коллекции `VARIATIONS`:

    ```python
    from paper_uploads.models import *

    class PageGallery(Collection):
        VARIATIONS = dict(
            mobile=dict(
                size=(640, 0),
                clip=False
            )
        )
        image = CollectionItem(ImageItem)
    ```

2) в дополнительных параметрах поля `CollectionItem` по ключу `variations`:

    ```python
    from paper_uploads.models import *

    class PageGallery(Collection):
        image = CollectionItem(ImageItem, options={
            'variations': dict(
                mobile=dict(
                    size=(640, 0),
                    clip=False
                )
            )
        })
    ```

Вариации, указанные первым способом (через `VARIATIONS` коллекции),
используются всеми классами элементов-изображений по умолчанию.
Но, если конкретный элемент коллекции объявляет свои собственные
вариации (вторым методом), то использовать он будет именно их.

### ImageCollection

Для коллекций, предназначенных исключительно для изображений,
"из коробки" доступна модель для наследования `ImageCollection`.
К ней уже подключен класс элементов-изображений.

```python
from paper_uploads.models import *


class PageGallery(ImageCollection):
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
```

---

Наследование от `Collection` на самом деле создает
[proxy-модель](https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models).
Это позволяет не создавать для каждой коллекции отдельную
таблицу в БД, но делает невозможным добавление к модели коллекции
дополнительных полей.

Чтобы экземпляры коллекций не смешивались при выполнении SQL-запросов,
менеджер `objects` в классе `Collection` был переопределен для того,
чтобы принимать во внимание `ContentType` коллекции и выполнять операции
только над теми коллекциями, класс которых соответствует текущему.

```python
# Вернет только экземпляры класса MyCollection
MyCollection.objects.all()

# Вернет абсолютно все экземпляры коллекций, всех классов
MyCollection._base_manager.all()
```

## Programmatically upload files
```python
from paper_uploads.models import *


# file / image
with open('file.doc', 'rb') as fp:
    file = UploadedFile()
    file.attach_file(fp)
    file.save()


# gallery
gallery = PageGallery.objects.create()
with open('image.jpg', 'rb') as fp:
    item = ImageItem()
    item.attach_to(gallery)
    item.attach_file(fp)
    item.save()
```

## Management Commands
#### check_uploads
Запускает комплексную проверку загруженных файлов
и выводит результат.

Список производимых тестов:
* загруженный файл существует в файловой системе
* для изображений существуют все файлы вариаций
* модель-владелец (указанная в `owner_app_label`
и `owner_model_name`) существует
* в модели-владельце существует поле `owner_fieldname`
* существует единственный экземпляр модели-владельца
со ссылкой на файл
* у элементов коллекций указан существующий и допустимый
`item_type`
* модель элементов коллекций идентична указанной
для `item_type`

При указании ключа `--fix-missing` все отсутствующие
вариации изображений будут автоматически перенарезаны
из исходников.

```shell
python3 manage.py check_uploads --fix-missing
```

#### clean_uploads
Находит мусорные записи в БД (например те, у которых
нет владельца) и предлагает их удалить.

Ссылка на загруженный файл создается в момент отправки формы
в админке. Из-за этого, в течение некоторого времени файл
будет являться "сиротой". Для того, чтобы такие файлы не удалялись,
по-умолчанию установлен фильтр, отсеивающий все файлы, загруженные
за последние 30 минут. Указать свой интервал фильтрации
(в минутах) можно через ключ `--min-age`.

```shell
python3 manage.py clean_uploads --min-age=10
```

#### recreate_variations
Перенарезает вариации для указанных моделей.

Рекомендуется запускать в интерактивном режиме:
```shell
python3 manage.py recreate_variations --interactive
```

Возможен вызов и в неинтерактивном режиме. Для этого
необходимо указать модель в виде строки вида
`AppLabel.ModelName` и имя поля, ссылающегося на изображение.

```shell
python3 manage.py recreate_variations 'app.Page' 'image'
```

Если нужно перенарезать не все вариации, а только некоторые,
то их можно перечислить в параметре `--variations`.

```shell
python3 manage.py recreate_variations 'app.Page' 'image' --variations big small
```

Также, изображения можно перенарезать через код, для конкретных
экземпляров `UploadedImage` или `ImageItem`:
```python
# перенарезка `big` и `medium` вариаций поля ImageField
page.image.recut(['big', 'medium'])

# перенарезка всех вариаций для всех картинок галереи
for image in page.gallery.get_items('image'):
    image.recut()
```

## Validators
Для добавления ограничений на загружаемые файлы применяются
специальные валидаторы:
* `SizeValidator` - задает максимально допустимый размер
файла в байтах.
* `ExtensionValidator` - задает допустимые расширения файлов.
* `MimeTypeValidator` - задает допустимые MIME типы файлов.
* `ImageMinSizeValidator` - устанавливает минимальный размер
загружаемых изображений.
* `ImageMaxSizeValidator` - устанавливает максимальный размер
загружаемых изображений.

```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *
from paper_uploads.validators import *

class Page(models.Model):
    image = ImageField(_('image'), blank=True, validators=[
        SizeValidator(10 * 1024 * 1024),   # max 10Mb
        ImageMaxSizeValidator(800, 800)    # max dimensions 800x800
    ])


class PageGallery(Collection):
    file = CollectionItem(FileItem, validators=[
        SizeValidator(10 * 1024 * 1024),
    ])
```

## Variation versions
Допустим, у нас есть изображение, которое нужно отобразить в трех
вариантах: `desktop`, `tablet` и `mobile`. Если мы хотим поддерживать
дисплеи Retina, нам нужно добавить ещё три вариации
для размера `2x`. Если мы также хотим использовать формат `WebP`
(сохранив исходные изображения для обратной совместимости),
то общее количество вариаций достигает **12**.

Поскольку Retina-вариации отличаются от обычных только увеличенным
на постоянный коэффициент размером, а `WebP`-вариации — принудительной
конвертацией в формат `WebP`, мы можем создавать эти вариации
автоматически.

Для этого нужно объявить перечень версий, которые нужно
сгенерировать, в параметре вариации `versions`. Поддерживаются
следующие значения: `webp`, `2x`, `3x`, `4x`.

```python
class Page(models.Model):
    image = ImageField(_('image'), blank=True,
        variations=dict(
            desktop=dict(
                # ...
                versions={'webp', '2x', '3x'}
            )
        )
    )
```

Приведенный выше код создаст следующие вариации:
* `desktop` - оригинальная вариация
* `desktop_webp` - `WebP`-версия оригинальной вариации
* `desktop_2x` - Retina 2x
* `desktop_webp_2x` - `WebP`-версия Retina 2x
* `desktop_3x` - Retina 3x
* `desktop_webp_3x` - `WebP`-версия Retina 3x

**NOTE**: Суффикс для Retina всегда следует после суффикса `WebP`.

Если необходимо переопределить какие-то параметры дополнительной
вариации, то придётся объявлять вариацию явно — она переопределит
одноименную сгенерированную вариацию.

```python
class Page(models.Model):
    image = ImageField(_('image'), blank=True,
        variations=dict(
            desktop=dict(
                size=(800, 600),
                versions={'webp', '2x', '3x'}
            ),
            desktop_2x=dict(
                size=(1600, 1200),
                jpeg=dict(
                    quality=72
                )
            )
        )
    )
```

## Cloudinary
Во встроенном модуле `paper_uploads.cloudinary` описаны поля и классы,
позволяющие загружать файлы и картинки в облачный сервис Cloudinary.
В этом случае нарезка вариаций не имеет смысла и поэтому недоступна.

### Installation
1) `pip install cloudinary`
2) Добавить `paper_uploads.cloudinary` и `cloudinary` в `INSTALLED_APPS`.
    ```python
    INSTALLED_APPS = [
        # ...
        'paper_uploads',
        'paper_uploads.cloudinary',
        'cloudinary',
        # ...
    ]
    ```
3) Задать [данные учетной записи](https://github.com/cloudinary/pycloudinary#configuration) Cloudinary
    ```python
    CLOUDINARY = {
       'cloud_name': 'mycloud',
       'api_key': '012345678901234',
       'api_secret': 'g1rtyOCvm4tDIfCPFFuh4u1W0PC',
       'sign_url': True,
       'secure': True
    }
    ```

### Model fields
```python
from paper_uploads.cloudinary.models import *

class Page(models.Model):
    file = CloudinaryFileField(_('file'), blank=True)
    media = CloudinaryMediaField(_('media'), blank=True)
    image = CloudinaryImageField(_('image'), blank=True)
```

### Collections
В модуле объявлено три класса элементов коллекции:
`CloudinaryFileItem`, `CloudinaryImageItem` и
`CloudinaryMediaItem` (для аудио и видео).

**NOTE**: В отличие от библиотеки `PIL`, Cloudinary поддерживает
загрузку SVG-файлов как изображений. Поэтому для SVG-файлов отдельный
класс не нужен.

Классы элементов коллекций Cloudinary используются также как обычные:
```python
from paper_uploads.models import *
from paper_uploads.cloudinary.models import *


class PageFiles(Collection):
    image = CollectionItem(CloudinaryImageItem)
    file = CollectionItem(CloudinaryFileItem)


class Page(models.Model):
    files = CollectionField(PageFiles)
```

Также, как и для обычных коллекций, для Cloudinary объявлено
два класса готовых коллекций: `CloudinaryCollection`
и `CloudinaryImageCollection`. `CloudinaryCollection` может хранить
любые файлы, а `CloudinaryImageCollection` — только изображения.

```python
from paper_uploads.models import *
from paper_uploads.cloudinary.models import *


class PageFiles(CloudinaryCollection):
    pass


class PageGallery(CloudinaryImageCollection):
    pass


class Page(models.Model):
    files = CollectionField(PageFiles)
    gallery = CollectionField(PageGallery)
```

### Usage

Для вывода ссылки на файл, загруженный в Cloudinary, библиотека содержит 
шаблонный тэг `paper_cloudinary_url`:

```djangotemplate
{% load paper_cloudinary %}

<img src={% paper_cloudinary_url page.image width=1024 crop=fill %}>
```

#### Jinja2
```jinja2
<img src={% paper_cloudinary_url page.image, width=1024, crop=fill %}>
```

Также доступна одноименная глобальная функция:
```jinja2
<img src={{ paper_cloudinary_url(page.image, width=1024, crop='fill') }}>
```

## Settings
Все настройки указываются в словаре `PAPER_UPLOADS`.

```python
PAPER_UPLOADS = {
    'STORAGE': 'django.core.files.storage.FileSystemStorage',
    'STORAGE_OPTIONS': {},
    'RQ_ENABLED': True,
    'VARIATION_DEFAULTS': {
        'jpeg': dict(
            quality=80,
            progressive=True,
        ),
        'webp': dict(
            quality=75,
        )
    }
}
```

### `STORAGE`
Путь к классу [хранилища Django](https://docs.djangoproject.com/en/2.2/ref/files/storage/).

Значение по умолчанию: `django.core.files.storage.FileSystemStorage`

### `STORAGE_OPTIONS`
Параметры инициализации хранилища.

Значение по умолчанию: `{}`

### `FILES_UPLOAD_TO`
Путь к папке, в которую загружаются файлы из FileField.
Может содержать параметры для даты и времени (см. [upload_to](https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.FileField.upload_to)).

Значение по умолчанию: `files/%Y-%m-%d`

### `IMAGES_UPLOAD_TO`
Путь к папке, в которую загружаются файлы из ImageField.

Значение по умолчанию: `images/%Y-%m-%d`

### `COLLECTION_FILES_UPLOAD_TO`
Путь к папке, в которую загружаются файлы коллекций.

Значение по умолчанию: `collections/files/%Y-%m-%d`

### `COLLECTION_IMAGES_UPLOAD_TO`
Путь к папке, в которую загружаются изображения коллекций.

Значение по умолчанию: `collections/images/%Y-%m-%d`

### `COLLECTION_ITEM_PREVIEW_WIDTH`, `COLLECTION_ITEM_PREVIEW_HEIGTH`
Размеры превью элементов коллекций в админке.

Значение по умолчанию: `180` x `135`

### `COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS`
Вариации, добавляемые к каждому классу изображений коллекций
для отображения превью в админке. Размеры файлов должны
совпадать с `COLLECTION_ITEM_PREVIEW_WIDTH` и
`COLLECTION_ITEM_PREVIEW_HEIGTH`.

### `RQ_ENABLED`
Включает нарезку картинок на вариации через отложенные задачи.
Требует наличие установленного пакета [django-rq](https://github.com/rq/django-rq).

Значение по умолчанию: `False`

### `RQ_QUEUE_NAME`
Название очереди, в которую помещаются задачи по нарезке картинок.

Значение по умолчанию: `default`

### `VARIATION_DEFAULTS`
Параметры вариаций по умолчанию.

Параметры, указанные в этом словаре, будут применены к каждой
вариации, если только вариация их явно не переопределяет.

Значение по умолчанию: `None`

### `CLOUDINARY_TYPE`
Тип загрузки файлов. Возможные значения: `private`, `upload`.
Значение по умолчанию: `private`

### `CLOUDINARY_TEMP_DIR`
Папка в разделе `/tmp/`, в которую скачиваются файлы из Cloudinary
при чтении их содержимого. Доступ к содержимому большого количества 
файлов из Cloudinary может привести к скачиванию больших объемов данных 
и захламлению временной папки.

### `CLOUDINARY_UPLOADER_OPTIONS`
Словарь, задающий глобальные [параметры загрузки](https://cloudinary.com/documentation/image_upload_api_reference#required_parameters)
для Cloudinary.

Значение по умолчанию:
```python
{
    'use_filename': True,
    'unique_filename': True,
    'overwrite': True,
    'invalidate': True
}
```

## Development and Testing
After cloning the Git repository, you should install this
in a virtualenv and set up for development:
```shell script
virtualenv .venv
source .venv/bin/activate
pip install -r ./requirements_dev.txt
pre-commit install
```

Install `npm` dependencies and build static files:
```shell script
npm i
npx webpack
```

Create `.env` file:
```.env
CLOUDINARY_URL=cloudinary://XXXXXXXXXXXXXXX:YYYYYYYYYYYYYYYYYYYYYYYYYYY@ZZZZZZ?sign_url=1&secure=1
```


[paper-admin]: https://github.com/dldevinc/paper-admin
[variations]: https://github.com/dldevinc/variations
[pycloudinary]: https://github.com/cloudinary/pycloudinary
[pilkit]: https://github.com/matthewwithanm/pilkit
[django-storages]: https://github.com/jschneier/django-storages
[django-rq]: https://github.com/rq/django-rq
