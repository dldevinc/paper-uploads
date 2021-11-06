# paper-uploads
Асинхронная загрузка файлов для административного интерфейса Django.

[![PyPI](https://img.shields.io/pypi/v/paper-uploads.svg)](https://pypi.org/project/paper-uploads/)
[![Build Status](https://travis-ci.org/dldevinc/paper-uploads.svg?branch=master)](https://travis-ci.org/dldevinc/paper-uploads)

![](http://joxi.net/gmvnGZBtqKOOjm.png)

## Requirements
* Python >= 3.6
* Django >= 2.2
* [paper-admin][paper-admin] >= 3.0
* [variations][variations]

## Features
* Каждый файл представлен своей моделью, что позволяет
хранить вместе с изображением дополнительные данные. 
Например, `alt` и `title`.
* Загрузка файлов происходит асинхронно и начинается сразу, 
при выборе файла в интерфейсе администратора.
* Поля модели, ссылающиеся на файлы, являются производными
от `OneToOneField` и не используют `<input type="file">`. 
Благодаря этому, при ошибках валидации формы, прикрепленные 
файлы не сбрасываются.
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

## Table of Contents

- [Installation](#Installation)
- [FileField](#FileField)
  - [UploadedFile](#UploadedFile)
- [ImageField](#ImageField)
  - [UploadedImage](#UploadedImage)
  - [Variations](#Variations)
  - [Manually creating variation files](#Manually-creating-variation-files)
  - [Using Redis Queue for variation update](#Using-Redis-Queue-for-variation-update)
  - [Variation versions](#Variation-versions)
- [Collections](#Collections)
  - [Collection items](#Collection-items)
  - [ImageCollection](#ImageCollection)
  - [Custom collection item classes](#Custom-collection-item-classes)
- [Programmatically upload files](#Programmatically-upload-files)
- [Management Commands](#Management-Commands)
- [Validators](#Validators)
- [Cloudinary](#Cloudinary)
  - [Installation](#Installation-1)
  - [Model fields](#Model-fields)
  - [Collections](#Collections-1)
  - [Usage](#Usage)
- [Settings](#Settings)

## Installation

Install `paper-uploads`:
```shell
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

# Add JS translations
PAPER_LOCALE_PACKAGES = [
   "django.contrib.admin",
   "paper_admin",
   "paper_uploads",
]
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

Поля модели:

| Поле | Тип         | Описание |
|------|-------------|----------|
| file | `FileField` | Ссылка на файл, хранящийся в Django-хранилище. |
| display_name | `CharField` | Удобочитаемое название файла для вывода на сайте.<br>Пример: `Отчёт за 2019 год`. |
| basename | `CharField` | Имя файла без пути, суффикса и расширения.<br>Пример: `my_document`. |
| extension | `CharField` | Расширение файла в нижнем регистре, без точки в начале.<br>Пример: `doc`. |
| size | `PositiveIntegerField` | Размер файла в байтах. |
| checksum | `CharField` | Контрольная сумма файла. Используется для отслеживания изменений файла. |
| created_at | `DateTimeField` | Дата создания экземпляра модели. |
| modified_at | `DateTimeField` | Дата изменения модели. |
| uploaded_at | `DateTimeField` | Дата загрузки файла. |

Свойства модели:

| Поле | Тип         | Описание |
|------|-------------|----------|
| name | `str` | Полное имя файла, передающееся в Django storage.<br>Пример: `files/my_document_19sc2Kj.pdf`. |

Для упрощения работы с загруженными файлами, некоторые методы и свойства
стандартного класса `FieldFile` проксированы на уровень модели:
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

Таким образом, вместо `page.report.file.url` можно использовать
`page.report.url`.

Поддерживается протокол контекстного менеджера:
```python
page = Page.objects.first()
with page.report.open() as fp:
    print(fp.read(10))
```

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
```

При загрузке изображения создается экземпляр модели `UploadedImage`.

### UploadedImage

Модель, представляющая загруженное изображение.

Поля модели:

| Поле | Тип         | Описание |
|------|-------------|----------|
| file | `FileField` | Ссылка на файл, хранящийся в Django-хранилище. |
| title | `CharField` | Название изображения, которое можно вставить в атрибут `title` тэга `<img>`. |
| description | `CharField` | Описание изображения, которое можно вставить в атрибут `alt` тэга `<img>`. |
| width | `PositiveSmallIntegerField` | Ширина загруженного изображения. |
| height | `PositiveSmallIntegerField` | Высота загруженного изображения. |
| basename | `CharField` | Имя файла без пути, суффикса и расширения.<br>Пример: `my_image`. |
| extension | `CharField` | Расширение файла в нижнем регистре, без точки в начале.<br>Пример: `jpg`. |
| size | `PositiveIntegerField` | Размер файла в байтах. |
| checksum | `CharField` | Контрольная сумма файла. Используется для отслеживания изменений файла. |
| created_at | `DateTimeField` | Дата создания экземпляра модели. |
| modified_at | `DateTimeField` | Дата изменения модели. |
| uploaded_at | `DateTimeField` | Дата загрузки файла. |

Свойства модели:

| Поле | Тип         | Описание |
|------|-------------|----------|
| name | `str` | Полное имя файла, передающееся в Django storage.<br>Пример: `images/my_image_19sc2Kj.jpg`. |

По аналогии с `FileField`, модель `UploadedImage` проксирует
методы и свойства стандартного класса `FieldFile`.

### Variations

Вариация - это дополнительное изображение, которое получается 
из оригинального путём заранее заданных трансформаций. 

Вариации описываются словарем `variations` поля `ImageField`:

```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *


class Page(models.Model):
    image = ImageField(_('image with variations'),
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

Со списком допустимых опций для вариаций можно ознакомиться 
в библитеке [variations](https://github.com/dldevinc/variations#usage).

К вариациям можно обращаться прямо из экземпляра `UploadedImage`:
```python
print(page.image.desktop.url)
```

### Manually creating variation files

Нарезка изображения на вариации происходит при его загрузке.
Объявление новых вариаций (равно как изменение существующих) для поля, 
в которое уже загружен файл, не приведёт к созданию новых файлов.

Для того, чтобы создать файлы для новых вариаций (либо перезаписать 
существующие вариации, в которые были внесены изменения) можно
поступить одним из ниже описанных способов.

1. Вызвать метод `recut()` (либо `recut_async()`) из экземпляра 
   `UploadedImage`:

   ```python
   page.image.recut()
   ```
   
   При вызове этого метода все файлы вариаций для указанного экземпляра 
   создаются заново.
   <br>
   <br>
   Можно явно указать имена вариаций, которые необходимо перезаписать:
   ```python
   page.image.recut(["desktop", "mobile"]) 
   ```

2. Выполнить management-команду `recreate_variations`:
   ```shell
   python3 manage.py recreate_variations app.page --field=report
   ```

   Эта команда сгенерирует вариации для всех экземпляров указанной модели.

### Using Redis Queue for variation update 

Если загрузка изображений происходит достаточно часто и количество вариаций
для каждого изображения велико, то процесс создания вариаций может занимать 
значительное время. Это может оказать негативное влияние на производительность 
веб-сервера и даже послужить зоной для DoS-атаки.

Для того, чтобы стабилизировать процесс загрузки изображений, рекомендуется
создавать вариации асинхронно, в отдельном процессе, с помощью 
[django-rq][django-rq].

```shell
pip install django-rq
```

```python
# settings.py
PAPER_UPLOADS = {
    # ...
    "RQ_ENABLED": True,
    "RQ_QUEUE_NAME": "default"
}
```

Теперь при загрузке изображения вместо метода `recut()` будет вызываться 
метод `recut_async()`. При его использовании, превью для админки генерируется 
синхронно, а все остальные вариации - через отложенную задачу, которая
помещается в очередь, указанную в опции `RQ_QUEUE_NAME`. 

### Variation versions

Допустим, у нас есть изображение, которое нужно отобразить в трех
вариантах: `desktop`, `tablet` и `mobile`. Если мы хотим поддерживать
дисплеи Retina, нам нужно добавить ещё три вариации для размера `2x`. 
Если мы также хотим использовать формат `WebP` (сохранив исходный формат 
для обратной совместимости), то общее количество вариаций достигает **12**.

Поскольку Retina-вариации отличаются от обычных только увеличенным
на постоянный коэффициент размером, а `WebP`-вариации — добавлением 
параметра `format = "webp"`, мы можем создавать эти вариации
автоматически. Это и есть версии вариации.

Перечень версий, которые нужно сгенерировать, указываются в параметре 
вариации `versions`. Поддерживаются следующие значения: 
`webp`, `2x`, `3x`, `4x`.

```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *


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

**NOTE**: Retina-суффикс всегда следует после суффикса `webp`, если
он есть.

Если необходимо переопределить какие-то параметры дополнительной
вариации, то придётся объявлять вариацию явно:

```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *


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

## Collections
Коллекция — это модель, группирующая экземпляры других моделей
(элементов коллекции). В частности, с помощью коллекции можно
создать фото-галерею или список файлов.

Для создания коллекции необходимо объявить класс, унаследованный
от `Collection` и указать модели элементов, которые могут входить
в коллекцию. Созданную коллекцию можно подключить к модели с 
помощью `CollectionField`:

```python
from django.db import models
from paper_uploads.models import *


# Collection model
class PageFiles(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)


# Target model
class Page(models.Model):
    files = CollectionField(PageFiles)

```

Класс `Collection` обладает особенным свойством: *любой дочерний
класс, унаследованный от `Collection`, является proxy-классом для
`Collection`*. 

В большинстве случаев коллекции отличаются друг от друга только 
набором элементов, которые могут входит в коллекцию. Использование
proxy-моделей предотвращает создание для каждой такой коллекции
отдельной таблицы в БД.

Как следствие, вы не можете добавлять собственные поля в классы
коллеций. Это ограничение можно снять, явно указав, что дочерний 
класс не должен быть proxy-моделью. В этом случае для коллекции 
будет создана отдельная таблица в БД.

```python
from django.db import models
from paper_uploads.models import *


class CustomCollection(Collection):
    file = CollectionItem(FileItem)

    name = models.CharField("name", max_length=128, blank=True)

    class Meta:
        proxy = False
```

### Collection items

Псевдо-поле `CollectionItem` подключает к коллекции модель элемента 
под заданным именем. Это имя сохраняется в БД при загрузке файла. 
По этой причине **не рекомендуется менять имена элементов коллекций,
если в неё уже загружены файлы**.

```python
from paper_uploads.models import *


class PageFiles(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)
```

В приведённом примере, коллекция `PageFiles` может содержать элементы 
трех классов: `SVGItem`, `ImageItem` и `FileItem`. Порядок подключения 
элементов коллекции имеет значение: первый класс, чей метод `file_supported()`
вернет `True`, определит модель загруженного файла. По этой причине 
`FileItem` должен указываться последним, т.к. он принимает любые файлы.

Вместе с моделью элемента, в поле `CollectionItem` можно указать
[валидаторы](#Validators):

```python
from paper_uploads.models import *
from paper_uploads.validators import SizeValidator


class FileCollection(Collection):
    file = CollectionItem(FileItem, validators=[
        SizeValidator(2 * 1000 * 1000)
    ])
```

---

В состав библиотеки входят следующие классы элементов:
* `ImageItem`. Для хранения изображения с возможностью нарезки
на вариации.
* `SVGItem`. Для хранения SVG иконок.
* `FileItem`. Может хранить любой файл.

Вариации для изображений коллекции можно указать двумя способами:
1) в атрибуте класса коллекции `VARIATIONS`:

    ```python
    from paper_uploads.models import *

    class PageGallery(Collection):
        image = CollectionItem(ImageItem)
        
        VARIATIONS = dict(
            mobile=dict(
                size=(640, 0),
                clip=False
            )
        )
    ```

2) в дополнительных параметрах поля `CollectionItem` по ключу `variations`:

    ```python
    from paper_uploads.models import *

    class PageGallery(Collection):
        image = CollectionItem(ImageItem, options={
            "variations": dict(
                mobile=dict(
                    size=(640, 0),
                    clip=False
                )
            )
        })
    ```

### ImageCollection

Для коллекций, предназначенных исключительно для изображений, из коробки
доступна модель для наследования `ImageCollection`. К ней уже подключен 
класс элементов-изображений.

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

### Custom collection item classes

При создании пользовательских классов элементов коллекций не рекомендуется
использовать прямое наследование от существующих моделей `FileItem`, `ImageItem` и т.п.
Это содзаёт сложные One2One-связи между коллекциями и элементами коллекций и может 
привести к `RecursionError` при удалении коллекций или их элементов.

Для того, чтобы избежать потенциальных проблем, в качестве базовых классов следует 
использовать абстрактные классы. Такие как `FileItemBase`, `ImageItemBase` или 
более общие `CollectionItemBase` и `CollectionFileItemBase`.

```python
from django.db import models
from paper_uploads.models import *


class CustomImageItem(ImageItemBase):
    caption = models.TextField(_("caption"), blank=True)


class CustomCollection(Collection):
    image = CollectionItem(CustomImageItem)
```

## Programmatically upload files

Для `FileField` и `ImageField`:
```python
from django.db import models
from paper_uploads.models import *


class Page(models.Model):
    report = FileField(_("report"))
    

# Поля `owner_*` формируют ссылку на поле модели, 
# с которым будет связан файл. Эти поля позволяют
# находить и удалять неиспользуемые файлы.
file = UploadedFile(
    owner_app_label=Page._meta.app_label,
    owner_model_name=Page._meta.model_name,
    owner_fieldname="report"
)

with open("file.doc", "rb") as fp:
    file.attach_file(fp)

file.save()

page = Page.objects.create(
    report=file
)
```

Для коллекций:
```python
from paper_uploads.models import *


class PageImages(ImageCollection):
    pass


gallery = PageImages.objects.create()

item = ImageItem()
item.attach_to(gallery)

with open("image.jpg", "rb") as fp:
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

Владелец загруженного файла устанавливается в момент сохранения страницы
в админке. А это происходит позже фактической загрузки файла на сервер. 
Как следствие, в течение некоторого времени файл будет являться "сиротой". 
Для того, чтобы такие файлы не удалялись, команда `clean_uploads` игнорирует
файлы, загруженные за последние 30 минут. Изменить интервал фильтрации
(в минутах) можно через ключ `--min-age`.

```shell
python3 manage.py clean_uploads --min-age=60
```

#### recreate_variations
Перенарезает вариации для указанных моделей.
Модель указывается в формате `app_label.model_name`.

Если модель является коллекцией, необходимо указать параметр `--item-type`:
```shell
python3 manage.py recreate_variations 'app.Photos' --item-type='image'
```

Для обычных моделей необходимо указать параметр `--field`:
```shell
python3 manage.py recreate_variations 'app.Page' --field='image'
```

По умолчанию перенарезаются все возможные вариации для каждого
экземпляра указанной модели. Можно указать конкретные вариации,
которые нужно перенарезать:
```shell
python3 manage.py recreate_variations 'app.Page' --field='image' --variations big small
```

#### remove_variations
Удаление файлов вариаций.
Параметры аналогичны параметрам `recreate_variations`.

```shell
python3 manage.py remove_variations 'app.Page' --field='image'
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
        SizeValidator(10 * 1000 * 1000),   # max 10Mb
        ImageMaxSizeValidator(800, 800)    # max dimensions 800x800
    ])


class PageGallery(Collection):
    file = CollectionItem(FileItem, validators=[
        SizeValidator(10 * 1000 * 1000),
    ])
```

## Cloudinary
Во встроенном модуле `paper_uploads.cloudinary` находятся поля и классы,
позволяющие загружать файлы и картинки в облачный сервис Cloudinary.

Помимо очевидной выгоды от хранения данных в облаке, использование
Cloudinary в качестве хранилища файлов даёт возможность пользоваться
API для трансформации [изображений](https://cloudinary.com/documentation/image_transformations)
и [медиа](https://cloudinary.com/documentation/video_manipulation_and_delivery).

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
   ```shell
   $ export CLOUDINARY_URL=cloudinary://API-Key:API-Secret@Cloud-name?sign_url=1&secure=1
   ``` 

Чтобы предотвратить генерацию трасформаций конечными пользователями, рекомендуется
включить в вашем аккаунте Cloudinary [Strict transformations](https://cloudinary.com/documentation/control_access_to_media#strict_transformations).

### Model fields

Вместо `FileField` и `ImageField` используются поля `CloudinaryFileField`,
`CloudinaryImageField` и `CloudinaryMediaField`.

```python
from django.db import models
from paper_uploads.cloudinary.models import *

class Page(models.Model):
    file = CloudinaryFileField(_('file'), blank=True)
    image = CloudinaryImageField(_('image'), blank=True)
    media = CloudinaryMediaField(_('media'), blank=True)
```

Дополнительные [параметры загрузки Cloudinary](https://cloudinary.com/documentation/image_upload_api_reference#upload_optional_parameters) 
можно задать с помощью параметра `cloudinary`:
```python
from django.db import models
from paper_uploads.cloudinary.models import *


class Page(models.Model):
    file = CloudinaryFileField(_('file'), blank=True, cloudinary={
        "use_filename": False
    })
```

### Collections

Для коллекций используется тот же класс `Collection`, что используется
при локальном хранении файлов. Отличаются только классы элементов коллекций.

В состав библиотеки входит три класса элементов коллекции:
`CloudinaryFileItem`, `CloudinaryImageItem` и `CloudinaryMediaItem` 
(для аудио и видео).

```python
from django.db import models
from paper_uploads.models import *
from paper_uploads.cloudinary.models import *


class PageFiles(Collection):
    image = CollectionItem(CloudinaryImageItem)
    file = CollectionItem(CloudinaryFileItem)


class Page(models.Model):
    files = CollectionField(PageFiles)
```

Также, как и для обычных коллекций, для Cloudinary объявлена готовая 
коллекция для изображений &mdash; `CloudinaryImageCollection`:

```python
from django.db import models
from paper_uploads.models import *
from paper_uploads.cloudinary.models import *


class PageGallery(CloudinaryImageCollection):
    pass


class Page(models.Model):
    gallery = CollectionField(PageGallery)
```

### Usage

Для вывода ссылки на файл, загруженный в Cloudinary, библиотека содержит 
шаблонный тэг `paper_cloudinary_url`:

```djangotemplate
{% load paper_cloudinary %}

<img src={% paper_cloudinary_url page.image width=1024 crop=fill %}>
```

Для `jinja2`:
```jinja2
<img src={% paper_cloudinary_url page.image, width=1024, crop=fill %}>
```

Также, для `jinja2` доступна одноименная глобальная функция:
```jinja2
<img src={{ paper_cloudinary_url(page.image, width=1024, crop='fill') }}>
```

## Customize upload folder 

По умолчанию, папки для загружаемых файлов задаются глобально, в настройках:
```python
PAPER_UPLOADS = {
    # ...
    "FILES_UPLOAD_TO": "files/%Y-%m-%d",
    "IMAGES_UPLOAD_TO": "images/%Y-%m-%d",
    "COLLECTION_FILES_UPLOAD_TO": "collections/files/%Y-%m-%d",
    "COLLECTION_IMAGES_UPLOAD_TO": "collections/images/%Y-%m-%d",
}
```

Для того, чтобы загружаемые файлы помещались в отдельную папку для конкретного 
поля, необходимо переопределить метод `get_file_folder`:

```python
from django.db import models
from paper_uploads.models import *


class CustomUploadedFile(UploadedFile):
    class Meta:
        proxy = True

    def get_file_folder(self) -> str:
        return "custom-files/%Y-%m-%d"


class Page(models.Model):
    file = FileField(_("file"), to=CustomUploadedFile)

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
Требует наличие установленного пакета [django-rq][django-rq].

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
PAPER_UPLOADS = {
    "CLOUDINARY_UPLOADER_OPTIONS": {
        "use_filename": True,
        "unique_filename": True,
        "overwrite": True,
        "invalidate": True
    }
}
```

## Development and Testing
After cloning the Git repository, you should install this
in a virtualenv and set up for development:
```shell script
virtualenv .venv
source .venv/bin/activate
pip install -r ./requirements.txt
pre-commit install
```

Install `npm` dependencies and build static files:
```shell script
npm ci
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
