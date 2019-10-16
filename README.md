# paper-uploads

![](http://joxi.net/gmvnGZBtqKOOjm.png)

Предоставляет поля для асинхронной загрузки файлов.

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
от OneToOneField и не используют `<input type="file">`. Благодаря
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
* Возможность создавать коллекции разнородных элементов 
(галереи, коллекции файлов и т.п.).
* Возможность сортировать элементы коллекций.

## Installation
```python
INSTALLED_APPS = [
    # ...
    'paper_uploads',
    # ...
]

PAPER_UPLOADS = {
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
Поле для загрузки файла.

Никаких ограничений на загружаемые файлы по-умолчанию нет. 
Но их можно добавить с помощью [валидаторов](#Validation).

```python
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *
from paper_uploads.validators import *


class Page(models.Model):
    file = FileField(_('file'), blank=True, validators=[
        SizeValidator(10*1024*1024)    # up to 10Mb    
    ])
```

При загрузке файла создается экземпляр модели `UploadedFile`. Помимо самого
файла, хранящегося в поле `file`, предоставляются следующие поля:
* `name` - имя файла без расширения и суффикса, добавляемого `FileStorage`.
* `display_name`- имя файла для вывода на сайте.
* `extension` - расширение файла с нижнем регистре.
* `size` - размер файла в байтах.
* `hash` - SHA-1 хэш содержимого файла.
* `created_at` - дата создания экземпляра модели.
* `uploaded_at` - дата загрузки файла.
* `modified_at` - дата изменения модели.

Модели, унаследованные от `UploadedFileBase`, проксируют некоторые свойства 
`FileField` на уровень модели:
* `url`
* `path`
* `open`
* `read`
* `close`
* `closed`

Таким образом, вместо `Page.file.file.url` можно использовать `Page.file.url`.

## ImageField
Поле для загрузки изображений. 

Поддерживает нарезку на неограниченное количество вариаций. 
Настройки вариаций задаются словарем `variations`. Доступные параметры
можно посмотреть в модуле [variations](https://github.com/dldevinc/variations).

Исходное загруженное изображение сохраняется в файловой системе без
изменений. При добавлении новых вариаций или изменении существующих, 
можно заново произвести нарезку с помощью команды [recreate_variations](#recreate_variations).

```python
from pilkit import processors
from django.db import models
from django.utils.translation import ugettext_lazy as _
from paper_uploads.models import *


class Page(models.Model):
    image = ImageField(_('single image'), blank=True)
    varsatile_image = ImageField(_('image with variations'), blank=True,
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

При загрузке изображения создается экземпляр модели `UploadedImage`. Помимо 
исходного изображения, хранящегося в поле `file`, предоставляются следующие поля:
* `name` - имя файла без расширения и суффикса, добавляемого `FileStorage`.
* `extension` - расширение файла с нижнем регистре.
* `size` - размер файла в байтах.
* `hash` - SHA-1 хэш содержимого файла.
* `alt` - текст аттрибута `alt` для тэга `<img>`.
* `title` - текст аттрибута `title` для тэга `<img>`.
* `width` - ширина исходного изображения в пикселях.
* `height` - высота исходного изображения в пикселях.
* `created_at` - дата создания экземпляра модели.
* `uploaded_at` - дата загрузки файла.
* `modified_at` - дата изменения модели.

К вариациям можно обращаться прямо из экземпляра `UploadedImage`:
```python
page.image_ext.desktop.url
```

## Collections
Коллекция - это модель, группирующая экземпляры других моделей (элементов 
коллекции). В частности, с помощью коллекции можно создать галерею 
изображений или список файлов.

Для создания коллекции необходимо создать класс, унаследованый 
от `Collection` и объявить модели элементов, которые могут входить
в коллекцию. Синтаксис объявления элементов подобен добавлению полей:

```python
from paper_uploads.models import *


class PageFiles(Collection):
    svg = CollectionItemTypeField(SVGItem)
    image = CollectionItemTypeField(ImageItem)
    file = CollectionItemTypeField(FileItem)
``` 

Псевдо-поле `CollectionItemTypeField` подключает модель
элемента к коллекции под заданным именем, которое сохраняется 
в базу данных (в поле `item_type`) вместе с загруженным файлом. 
При изменении имен, под которыми поключены элементы, или при 
добавлении новых элементов к существующим коллекциям, разработчик 
должен убедиться в том, что БД останется в согласованном состоянии.

Вместе с моделью элемента, в поле `CollectionItemTypeField`
можно передать [валидаторы](#Validators) и дополнительные параметры 
(в словаре `options`), которые могут быть использованы для
более детальной настройки элемента коллекции.

Порядок подключения элементов к коллекции имеет значение: первый 
класс элемента, чей метод `file_supported()` вернет `True`, 
определит модель загружаемого файла. Поэтому `FileItem` должен 
указываться последним, т.к. он принимает любые файлы.

Полученную коллекцию можно подключать к моделям с помощью 
`CollectionField`:

```python
from django.db import models
from paper_uploads.models import *


class Page(models.Model):
    gallery = CollectionField(PageFiles)
```

---

Классы элементов наследуются от `CollectionItemBase`. В состав 
библиотеки входят следующие готовые классы элементов:
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
        image = CollectionItemTypeField(ImageItem)
    ```
   
2) ключ `variations` словаря `options` поля `CollectionItemTypeField`:

    ```python
    from paper_uploads.models import *
    
    class PageGallery(Collection):
        image = CollectionItemTypeField(ImageItem, options={
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
Она уже включает в себя класс элементов для картинок.

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
Это позволяет не создавать для каждой коллекции отдельную таблицу в БД.
А переопределенный менеджер `objects` в классе `Collection` позволяет 
прозрачно работать с коллекциями требуемого класса.

```python
# Вернет только экземпляры класса MyCollection
MyCollection.objects.all()

# Вернет абсолютно все экземпляры коллекций, всех классов
MyCollection._base_manager.all()
```

## Programmatically upload files
```python
from django.core.files import File
from paper_uploads.models import *


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

При указании ключа `--fix-missing` все отстутствующие 
вариации изображений будут автоматически перенарезаны из исходников.

```shell
python3 manage.py check_uploads --fix-missing
```

#### clean_uploads
Находит мусорные записи в БД (например те, у которых 
нет владельца) и предлагает их удалить.

С момента асинхронной загрузки в админке
до момента отправки формы файл является "сиротой", т.е
отсутсвует модель, ссылающаяся на него. 
Для того, чтобы такие файлы не удалялись, по-умолчанию
установлен фильтр, отсеивающий все файлы, загруженные за 
последние 30 минут. Указать свой интервал фильтрации
(в минутах) можно через ключ `--since`.  

```shell
python3 manage.py clean_uploads --since=10
```

#### recreate_variations
Перенарезает вариации для указанных моделей.

Рекоммендуется запускать в интерактивном режиме:
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
Для добавления ограничений на загружаемые файлы используются 
специальные валидаторы:
* `SizeValidator` - задает максимально допустимый размер 
файла в байтах.
* `ExtensionValidator` - задает допустимые расширения файлов.
* `MimetypeValidator` - задает допустимые mimetype-типы файлов.
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
    file = CollectionItemTypeField(FileItem, validators=[
        SizeValidator(10 * 1024 * 1024), 
    ])
```

## Postprocessing

Для каждого формата изображения можно указать команду, которая
будет выполнена для вариации сразу после её создания. Это
позволяет произвести оптимизации, которые выходят за рамки 
библиотеки `PIL`. 

Команды постобработки могут быть указаны глобально - в словаре
`POSTPROCESS` настроек библиотеки. Ключом является название 
формата, как это принято в `PIL` (поэтому, в частности, 
нужно писать `JPEG`, а не `JPG`). В качестве значения используется
словарь, в котором *должен* присутствовать ключ `command`
(в любом регистре), ссылающийся на исполняемый файл.

```python
PAPER_UPLOADS = {
    'POSTPROCESS': {
        'JPEG': {
            'COMMAND': 'jpeg-recompress',
            'ARGUMENTS': '--quality high --method smallfry {file} {file}',
        },
        'PNG': {
            'COMMAND': 'pngquant',
            'ARGUMENTS': '--force --skip-if-larger --output {file} {file}'
        },
    }
}
```

Опционально, в ключе `arguments` (в любом регистре) можно указать 
аргументы, передающиеся исполняемому файлу. В строке агрументов 
можно использовать шаблонную переменную `{file}`, которая будет
заменена на абсолютный путь к файлу вариации.

Помимо этого есть возможность переопределить команду постобработки 
(или запретить её) в конкретной вариации. Для того, чтобы отменить
постобработку, можно передать параметр `postprocess` со значением 
`False`.

Пример: отмена постобработки для всех форматов вариации, кроме 
JPEG. Для JPEG будет использована команда `echo`:
```python
from django.db import models
from paper_uploads.models import *


class Page(models.Model):
    image = ImageField(_('image'), blank=True,
        variations=dict(
            desktop=dict(
                size=(1600, 0),
                postprocess=False,  # disable any postprocessing ...
                jpeg=dict(
                    quality=92,
                    postprocess={   # ... except for JPEG
                        'command': 'echo',
                        'arguments': '"{file}"'
                    }       
                ),
            )
        )
    )
```

**NOTE**: не путайте настройки постобработки файла `postprocess`
с `pilkit`-процессорами, указываемыми в параметре `postprocessors`.

## Settings
Все настройки указываются в словаре `PAPER_UPLOADS`.

```python
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

### DEFAULT_FACE_DETECTION
Включает механизм центрирования по лицам при обрезке изображений
для всех вариаций по умолчанию. Должна быть установлена библиотека
[face_recognition](https://github.com/ageitgey/face_recognition):

```shell script
pip install face_recognition
```

Для конкретных вариаций можно разрешить или запретить центрирование
с помощью параметра вариации `face_detection`.

Значение по умолчанию: `False`

### RQ_ENABLED
Включает нарезку картинок на вариации через отложенные задачи.
Требует наличие установленного пакета [django-rq](https://github.com/rq/django-rq).

Значение по умолчанию: `False`

### RQ_QUEUE_NAME
Название очереди, в которую помещаются задачи по нарезке картинок. 

Значение по умолчанию: `default`

### POSTPROCESS
Словарь, задающий shell-команды, запускаемые после загрузки 
изображений. Для каждого формата изображения можно указать 
свою команду.

Ключами словаря являются названия выходных форматов изображений
в верхнем регистре. Например: `JPEG`, `PNG`, `GIF`, `WEBP`.
Перечень допустимых форматов ограничен поддрживаемыми форматами 
библиотеки [Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)).

Для оптимизации SVG можно воспользоваться специальным ключом `SVG`.
Он будет работать только для SVG-изображений, загруженных в коллекции.
Для SVG-файлов из `FileField` он работать не будет.

Значение по умолчанию: `{}`
