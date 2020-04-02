# paper-uploads

[![PyPI-Server](https://badge.fury.io/py/paper-uploads.svg)](https://pypi.org/project/paper-uploads/)

![](http://joxi.net/gmvnGZBtqKOOjm.png)

Предоставляет поля для асинхронной загрузки файлов.

## Requirements
* Python 3.5+
* Django 2.1+
* [paper-admin](https://github.com/dldevinc/paper-admin)
* [variations](https://github.com/dldevinc/variations)

## Features
* Каждый файл представлен своей моделью, что позволяет 
хранить метаданные. Например, alt и title для изображения.
* Загрузка файлов происходит асинхронно.
* Поля для хранения файлов являются производными 
от `OneToOneField` и не используют `<input type="file">`. Благодаря 
этому, при ошибках валидации прикрепленные файлы не сбрасываются.
* Совместимость с [django-storages](https://github.com/jschneier/django-storages).
* Опциональная интеграция с [Cloudinary](https://cloudinary.com/documentation/cloudinary_references).
* Загруженные картинки можно нарезать на множество вариаций.
Каждая вариация гибко настраивается. Можно указать размеры, 
качество сжатия, формат, добавить дополнительные 
[pilkit](https://github.com/matthewwithanm/pilkit)-процессоры, 
распознавание лиц и другое. См. 
[variations](https://github.com/dldevinc/variations).
* Интеграция с [django-rq](https://github.com/rq/django-rq)
для отложенной нарезки картинок на вариации.
* Возможность постобработки изображений консольными утилитами. 
Такими как `mozjpeg` и `pngquant`.
* Возможность создавать коллекции файлов. В частности, галерей изображений с 
возможностью сортировки элементов.

## Installation
```python
INSTALLED_APPS = [
    # ...
    'paper_uploads',
    # ...
]

PAPER_UPLOADS = {
    'VARIATION_DEFAULTS': {
        'jpeg': dict(
            quality=80,
            progressive=True,
        ),
        'webp': dict(
            quality=75,
        )
    },
    'POSTPROCESS': {
        'jpeg': {
            'command': 'jpeg-recompress',
            'arguments': '--quality high "{file}" "{file}"',
        },
        'png': {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
        },
        'svg': {
            'command': 'svgo',
            'arguments': '--precision=4 --disable=convertPathData "{file}"',
        },   
    }
}
```

## FileField
Поле для загрузки файла.

На загружаемые файлы можно наложить ограничения с помощью [валидаторов](#Validation).
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
Помимо самого файла, хранящегося в поле `file`, модель предоставляет 
следующие поля:
* `name` - имя файла без расширения и суффикса, добавляемого `FileStorage`.
Пример: `my_document`.
* `display_name`- удобочитаемое название файла для вывода на сайте.
Пример: `Отчёт за 2019 год`.
* `extension` - расширение файла в нижнем регистре. Пример: `doc`.
* `size` - размер файла в байтах.
* `hash` - SHA-1 хэш содержимого файла.
* `created_at` - дата создания экземпляра модели.
* `uploaded_at` - дата загрузки файла.
* `modified_at` - дата изменения модели.

Модели файлов (`UploadedFile`, `UploadedImage` и модели элементов коллекций) 
проксирует некоторые аттрибуты и методы файла на уровень модели:
* `url`
* `path`
* `open`
* `close`
* `closed`
* `read`
* `seek`
* `tell`

Таким образом, вместо `Page.report.file.url` можно использовать 
`Page.report.url`.

## ImageField
Поле для загрузки изображений. 

Поддерживает нарезку на неограниченное количество вариаций. 
Настройки вариаций задаются в словаре `variations`. Синтаксис вариаций 
можно посмотреть в модуле [variations](https://github.com/dldevinc/variations).

Исходное загруженное изображение сохраняется в файловой системе без 
изменений. При добавлении новых вариаций или изменении существующих, 
можно заново произвести нарезку с помощью команды 
[recreate_variations](#recreate_variations).

```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *


class Page(models.Model):
    image = ImageField(_('single image'), blank=True)
    versatile_image = ImageField(_('image with variations'),
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
Помимо исходного изображения, хранящегося в поле `file`, 
модель предоставляет следующие поля:
* `name` - имя файла без расширения и суффикса, добавляемого `FileStorage`.
Пример: `summer_photo`.
* `extension` - расширение файла в нижнем регистре. Пример: `jpg`.
* `title` - текст аттрибута `title` для тэга `<img>`.
* `description` - текст аттрибута `alt` для тэга `<img>`.
* `width` - ширина исходного изображения в пикселях.
* `height` - высота исходного изображения в пикселях.
* `size` - размер файла в байтах.
* `hash` - SHA-1 хэш содержимого файла.
* `created_at` - дата создания экземпляра модели.
* `uploaded_at` - дата загрузки файла.
* `modified_at` - дата изменения модели.

К вариациям можно обращаться прямо из экземпляра `UploadedImage`:
```python
page.versatile_image.desktop.url
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
    svg = ItemField(SVGItem)
    image = ItemField(ImageItem)
    file = ItemField(FileItem)
``` 

Псевдо-поле `ItemField` подключает модель 
элемента к коллекции под заданным именем, которое сохраняется 
в базу данных (в поле `item_type`) вместе с загруженным файлом. 
При изменении имен псевдо-полей или при добавлении новых классов 
элементов к существующим коллекциям, разработчик должен самостоятельно 
обеспечить согласованное состояние БД.

Вместе с моделью элемента, в поле `ItemField` можно указать 
[валидаторы](#Validators) и дополнительные параметры 
(в словаре `options`), которые могут быть использованы для 
более детальной настройки элемента коллекции.

Порядок подключения классов элементов к коллекции имеет значение: 
первый класс, чей метод `file_supported()` вернет `True`, 
определит модель загружаемого файла. Поэтому `FileItem` должен 
указываться последним, т.к. он принимает любые файлы.

Полученную коллекцию можно подключать к моделям с помощью 
`CollectionField`:

```python
from django.db import models
from paper_uploads.models import *


class PageFiles(Collection):
    svg = ItemField(SVGItem)
    image = ItemField(ImageItem)
    file = ItemField(FileItem)


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
        image = ItemField(ImageItem)
    ```
   
2) в дополнительных параметрах поля `ItemField` по ключу `variations`:

    ```python
    from paper_uploads.models import *
    
    class PageGallery(Collection):
        image = ItemField(ImageItem, options={
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
* `MimetypeValidator` - задает допустимые MIME типы файлов.
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
    file = ItemField(FileItem, validators=[
        SizeValidator(10 * 1024 * 1024), 
    ])
```

## Postprocessing

Библиотека `paper-uploads` предоставляет возможность выполнения 
консольных команд над загруженными файлами. Для каждого отдельного 
формата указывается своя команда. Это позволяет произвести 
оптимизации, которые выходят за рамки стандартных средств Python.

**Постобработка выполняется только при использовании локального
хранилища `django.core.files.storage.FileSystemStorage`**.

Постобработка разделена на две группы: 
* изображения
* остальные файлы

### Options
Команды постобработки оформляются в виде словаря. 

Ключом словаря является название формата файла. Для изображений 
в качестве имени формата принято название, используемое в 
библиотеке [Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).
В частности, это означает что нужно писать `jpeg`, а не `jpg`.
Для остальных файлов, имя формата — это расширение файла.

Значением является словарь, в котором *должен* присутствовать 
ключ `command`, содержащий путь к исполняемому файлу. 
Опционально, в ключе `arguments` можно указать дополнительные 
аргументы для команды. В строке аргументов можно использовать 
шаблонную переменную `{file}`, которая будет заменена на 
абсолютный путь к файлу вариации.

Команды постобработки могут быть указаны глобально - в словаре
`POSTPROCESS` настроек библиотеки:
```python
PAPER_UPLOADS = {
    'POSTPROCESS': {
        'jpeg': {
            'command': 'jpeg-recompress',
            'arguments': '--quality high "{file}" "{file}"',
        },
        'png': {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
        },
    }
}
```

Для отмены постобработки необходимо указать значение `False`
в качестве значения параметра `postprocess` вариации.

### Image postprocessing

Постобработка применяется только к вариациям. Исходники изображений 
и изображения без вариаций остаются нетронутыми.

Вариация может переопределить глобальные команды постобработки.
Например, отменить любую постобработку:
```python
class Page(models.Model):
    image = ImageField(_('image'), blank=True,
        variations=dict(
            desktop=dict(
                # ...
                postprocess=False,
            )
        )
    )
```

Или переопределить постобработку для каждого формата отдельно:
```python
class Page(models.Model):
    image = ImageField(_('image'), blank=True,
        variations=dict(
            desktop=dict(
                # ...
                postprocess=dict(
                    jpeg=False,     # disable
                    webp={          # override
                        'command': 'echo',
                        'arguments': '"{file}"',
                    }                
                )
            )
        )
    )
```

**NOTE**: не путайте настройки постобработки `postprocess`
с `pilkit`-процессорами, указываемыми в параметре `postprocessors`.

В коллекциях переопределить команду можно через 
псевдо-поле `ItemField`:
```python
class PageFiles(Collection):
    image = ItemField(ImageItem, postprocess={
        'jpeg': {
            'command': 'jpegtran',     
            'arguments': '"{file}"', 
        }              
    })
    file = ItemField(FileItem)
```

### Common postprocessing

Для файлов, которые не относятся к изображениям, тоже доступны 
команды постобработки. В этом случае "форматом" является расширение 
файла.

В отличие от изображений, где постобработка применяются только к 
вариациям, для остальных файлов обрабатывается сам загруженный файл.
Поэтому есть риск **безвозвратного повреждения** загруженного файла.

**NOTE**: при использовании [django-rq](https://github.com/rq/django-rq)
постобработка файлов будет происходить через отложенные задачи.
Из-за этого, при первоначальной загрузке, виджет будет отображать 
размер файла **до** обработки.

Переопределить команду постобработки можно в параметре `postprocess` 
поля `FileField`:
```python
class Page(models.Model):
    file = FileField(_('file'), postprocess={
        'svg': {
            'command': 'svgo',        
            'arguments': '--precision=4 "{file}"',        
        }           
    })
```

В коллекциях переопределить команду можно через 
псевдо-поле `ItemField`:
```python
class PageFiles(Collection):
    svg = ItemField(SVGItem, postprocess={
        'svg': {
            'command': 'svgo',     
            'arguments': '--precision=4 "{file}"', 
        }              
    })
    file = ItemField(FileItem)
```

## Variation versions
Допустим, у нас есть изображение, которое нужно отобразить в трех 
вариантах: `desktop`, `tablet` и `mobile`. Если мы хотим поддерживать 
Retina дисплеи, нам нужно добавить ещё, как минимум, две вариации 
для размера `2x`. Если мы хотим ещё и использовать формат `WebP` с
обратной совместимостью, то общее количество вариаций умножается на 2 
и достигает 10.

Поскольку Retina-вариации отличаются от обычных только увеличенным 
на постоянный коэффициент размером, а `WebP`-вариации — принудительной 
конвертацией в формат `WebP`, мы можем создавать эти вариации 
автоматически. 

Для объявления вариации, имеющей несколько версий, нужно указать 
алиасы этих версий в параметре `versions`. Комбинируя эти алиасы 
между собой, библиотека создаст дополнительные *неявные* вариации.

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

Поддерживаются следующие алиасы вариаций: `webp`, `2x`, `3x`, `4x`.
Каждая неявная вариация является полноценной и обладает 
точно такими же свойствами, что и любая другая вариация. 

Если необходимо переопределить какие-то параметры дополнительной 
вариации, то придётся объявлять вариацию явно — она всегда перезапишет 
одноименную дополнительную вариацию.

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
В этом случае постобработка и нарезка вариаций не имеют смысла, 
и поэтому отключены.

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
       'api_secret': 'g1rtyOCvm4tDIfCPFFuh4u1W0PC'
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
    image = ItemField(CloudinaryImageItem)
    file = ItemField(CloudinaryFileItem)


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
В шаблонах доступен Jinja2-аналог шаблонного тэга `cloudinary_url`,
входящего в состав библиотеки [cloudinary](https://github.com/cloudinary/pycloudinary).
```jinja2
<img src={% cloudinary_url page.image width=1024 crop=fill %}>
```

Также доступна одноименная глобальная функция:
```jinja2
<img src={{ cloudinary_url(page.image, width=1024, crop='fill') }}>
```

## Settings
Все настройки указываются в словаре `PAPER_UPLOADS`.

```python
PAPER_UPLOADS = {
    'RQ_ENABLED': True,
    'VARIATION_DEFAULTS': {
        'jpeg': dict(
            quality=80,
            progressive=True,
        ),
        'webp': dict(
            quality=75,
        )
    },
    'POSTPROCESS': {
        'jpeg': {
            'command': 'jpeg-recompress',
            'arguments': '--quality high "{file}" "{file}"',
        },
        'png': {
            'command': 'pngquant',
            'arguments': '--force --skip-if-larger --output "{file}" "{file}"'
        },
        'svg': {
            'command': 'svgo',
            'arguments': '--precision=4 "{file}"',
        },   
    }
}
```

### STORAGE
Путь к классу [хранилища Django](https://docs.djangoproject.com/en/2.2/ref/files/storage/).

Значение по умолчанию: `django.core.files.storage.FileSystemStorage`

### STORAGE_OPTIONS
Параметры инициализации хранилища.

Значение по умолчанию: `{}`

### FILES_UPLOAD_TO
Путь к папке, в которую загружаются файлы из FileField.
Может содержать параметры для даты и времени (см. [upload_to](https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.FileField.upload_to)). 

Значение по умолчанию: `files/%Y-%m-%d`

### IMAGES_UPLOAD_TO
Путь к папке, в которую загружаются файлы из ImageField.

Значение по умолчанию: `images/%Y-%m-%d`

### COLLECTION_FILES_UPLOAD_TO
Путь к папке, в которую загружаются файлы коллекций.

Значение по умолчанию: `collections/files/%Y-%m-%d`

### COLLECTION_IMAGES_UPLOAD_TO
Путь к папке, в которую загружаются изображения коллекций.

Значение по умолчанию: `collections/images/%Y-%m-%d`

### COLLECTION_ITEM_PREVIEW_WIDTH, COLLECTION_ITEM_PREVIEW_HEIGTH
Размеры превью элементов коллекций в админке.

Значение по умолчанию: `144` x `108`

### COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS
Вариации, добавляемые к каждому классу изображений коллекций 
для отображения превью в админке. Размеры файлов должны 
совпадать с `COLLECTION_ITEM_PREVIEW_WIDTH` и 
`COLLECTION_ITEM_PREVIEW_HEIGTH`.

### RQ_ENABLED
Включает нарезку картинок на вариации через отложенные задачи.
Требует наличие установленного пакета [django-rq](https://github.com/rq/django-rq).

Значение по умолчанию: `False`

### RQ_QUEUE_NAME
Название очереди, в которую помещаются задачи по нарезке картинок. 

Значение по умолчанию: `default`

### VARIATION_DEFAULTS
Параметры вариаций по умолчанию.

Параметры, указанные в этом словаре, будут применены к каждой 
вариации, если только вариация их явно не переопределяет.

Значение по умолчанию: `{}`

### POSTPROCESS
Словарь, задающий shell-команды, запускаемые после загрузки 
файлов. Для каждого формата можно указать свою команду.

Ключами словаря являются названия форматов файлов.
Например: `jpeg`, `png`, `gif`, `webp`, `svg`.

Значение по умолчанию: `{}`

### CLOUDINARY
Словарь, задающий глобальные [параметры загрузки](https://cloudinary.com/documentation/image_upload_api_reference#required_parameters)
для cloudinary.

Значение по умолчанию: 
```python
{
    'use_filename': True,
    'unique_filename': True,
    'overwrite': True,
}
```
