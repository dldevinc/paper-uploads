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

Исходное загруженное изображение сохраняется в файловой системе без
изменений. При добавлении новых вариаций или изменении существующих, 
можно заново произвести нарезку с помощью команды [recreate_variations](#recreate_variations).

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
Для создания коллекции необходимо создать класс модели коллекции, 
унаследованый от `Collection` или `ImageCollection`.

Коллекция может включать элементы любого вида, который можно 
описать с помощью модели, унаследованной от `CollectionItemBase`. 
Перечень допустимых классов элементов задается с помощью 
`CollectionItemTypeField`. Синтаксис подключения подобен добавлению 
поля `ForeignKey` к модели.

```python
from paper_uploads.models import collection
from paper_uploads.models.fields import CollectionItemTypeField


class PageFiles(collection.Collection):
    svg = CollectionItemTypeField(collection.SVGItem)
    image = CollectionItemTypeField(collection.ImageItem)
    file = CollectionItemTypeField(collection.FileItem)
```

Порядок подключения классов элементов имеет значение: при загрузке
файла через админку, его класс определется первым классом,
чей метод `check_file` вернет `True`. Поэтому элементы следует
объявлять от более конкретных к более общим. 

**Note**: Менять имена полей `CollectionItemTypeField` нельзя, т.к при 
добавлении нового элемента это имя заносится в БД.

---

Для коллекций, предназначенных исключительно для изображений, 
"из коробки" доступна модель для наследования `ImageCollection`,
с предустановленным фильтром mimetype на этапе выбора файла.

```python
from django.db import models
from paper_uploads.models import collection
from paper_uploads.models.fields import CollectionField, CollectionItemTypeField


class PageFiles(collection.Collection):
    svg = CollectionItemTypeField(collection.SVGItem)
    file = CollectionItemTypeField(collection.FileItem)


class PageImages(collection.ImageCollection):
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

Наследование от `Collection` на самом деле создает
[proxy-модель](https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models),
чтобы не плодить множество однотипных таблиц в БД. Благодаря 
переопределенному менеджеру `objects` в классе `Collection`, запросы 
через этот менеджер будут затрагивать только коллекции того же класса, 
от имени которого вызываются.

```python
# Вернет только экземпляры класса MyCollection
MyCollection.objects.all()

# Вернет абсолютно все экземпляры коллекций, всех классов
MyCollection._base_manager.all()
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
Запускает комплексную проверку загруженных файлов и выводит результат. 

Список производимых тестов:
* загруженный файл существует в файловой системе
* для изображений существуют все файлы вариаций
* модель-владелец (указанная в `owner_app_label` и `owner_model_name`) существует
* в модели-владельце существует поле `owner_fieldname`
* существует единственный экземпляр модели-владельца со ссылкой на файл
* у элементов коллекций указан существующий и допустимый `item_type`
* модель элементов коллекций идентична указанной для `item_type`

При указании ключа `--fix-missing` все отстутствующие 
вариации изображений будут автоматически перенарезаны из исходников.

```python
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

```python
python3 manage.py clean_uploads --since=10
```

#### recreate_variations
Перенарезает вариации для указанных моделей / полей.

Для перенарезки вариаций для какого-либо поля модели, необходимо
указать модель в виде строки вида `AppLabel.ModelName` и имя поля 
в параметре `--field`

```python
python3 manage.py recreate_variations 'page.Page' --field=image 
```

Для перенарезки всех изображений галереи достаточно указать
только модель.

```python
python3 manage.py recreate_variations 'page.PageGallery'
```

Если нужно перенарезать не все вариации, а только некоторые,
то их можно перечислить в параметре `--variations`.

```python
python3 manage.py recreate_variations 'page.PageGallery' --variations big small
```

## Validation
* `SizeLimitValidator` - устанавливает максимально допустимый
размер загружаемого файла в байтах.
* `ImageMinSizeValidator` - устанавливает минимальный размер загружаемых изображений.
* `ImageMaxSizeValidator` - устанавливает максимальный размер загружаемых изображений.

```python
from django.db import models
from paper_uploads.models import Collection, FileItem
from paper_uploads.models.fields import ImageField, CollectionItemTypeField 
from paper_uploads.validators import SizeValidator, ImageMaxSizeValidator

class Page(models.Model):
    image = ImageField(_('image'), blank=True, validators=[
        SizeValidator(10 * 1024 * 1024),   # max 10Mb
        ImageMaxSizeValidator(800, 800)     # max dimensions 800x800
    ])


class PageGallery(Collection):
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
| COLLECTION_FILES_UPLOAD_TO | Путь к папке, в которую загружаются файлы галереи. По умолчанию, `gallery/files/%Y-%m-%d` |
| COLLECTION_IMAGES_UPLOAD_TO | Путь к папке, в которую загружаются картинки галереи. По умолчанию, `gallery/images/%Y-%m-%d` |
| COLLECTION_ITEM_PREVIEW_WIDTH | Ширина превью элемента галереи в виджете админки. По-умолчанию, `144` |
| COLLECTION_ITEM_PREVIEW_HEIGHT | Высота превью элемента галереи в виджете админки. По-умолчанию, `108` |
| COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS | Вариации для превью картинок галереи в виджете админки. |
| RQ_ENABLED | Включает нарезку картинок на вариации через отложенные задачи. Требует наличие установленного пакета [django-rq](https://github.com/rq/django-rq) |
| RQ_QUEUE_NAME | Название очереди, в которую помещаются задачи по нарезке картинок. По-умолчанию, `default` |
| POSTPROCESS | Словарь, задающий команды, запускаемые после загрузки файла. Для каждого формата своя команда. |
