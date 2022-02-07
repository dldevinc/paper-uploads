# paper-uploads
Асинхронная загрузка файлов для административного интерфейса Django.

[![PyPI](https://img.shields.io/pypi/v/paper-uploads.svg)](https://pypi.org/project/paper-uploads/)
[![Build Status](https://github.com/dldevinc/paper-uploads/actions/workflows/tests.yml/badge.svg)](https://github.com/dldevinc/paper-uploads)
[![Software license](https://img.shields.io/pypi/l/paper-uploads.svg)](https://pypi.org/project/paper-uploads/)

## Requirements
* Python >= 3.6
* Django >= 2.2
* [paper-admin][paper-admin] >= 3.0
* [variations][variations]

## Features
* Каждый файл представлен своей моделью. Это позволяет хранить 
  вместе с файлом дополнительные данные. Например, `alt` для изображений.
* Загрузка файлов происходит асинхронно и начинается сразу 
  при выборе файла в интерфейсе администратора.
* Поля модели, предоставляемые библиотекой `paper-uploads`, 
  являются производными от `OneToOneField` и не используют 
  `<input type="file">`. Благодаря этому, при ошибках валидации формы
  прикрепленные файлы не сбрасываются.
* Загруженные картинки можно нарезать на множество вариаций.
  Каждая вариация гибко настраивается. Можно указать размеры,
  качество сжатия, формат, добавить дополнительные
  [pilkit][pilkit]-процессоры, распознавание лиц и прочее.
  <br>См. [variations][variations].
* Совместим с [django-storages][django-storages].
* Опциональная интеграция с [django-rq][django-rq]
  для отложенной нарезки картинок на вариации.
* Возможность создавать коллекции файлов. В частности, галерей 
  изображений с возможностью сортировки элементов.
* Внутренний подмодуль `paper_uploads.cloudinary` предоставляет 
  поля и классы, реализующие хранение файлов в облаке
  [Cloudinary][pycloudinary].

## Table of Contents

- [Installation](#Installation)
- [FileField](#FileField)
- [Validators](#Validators) 
- [UploadedFile](#UploadedFile)
- [Programmatically upload files](#Programmatically-upload-files)
- [ImageField](#ImageField)
- [UploadedImage](#UploadedImage)
  - [Variations](#Variations)
  - [Versions](#Versions)
  - [Redis Queue](#Redis Queue)
- [Collections](#Collections)
  - [Collection items](#Collection-items)
  - [ImageCollection](#ImageCollection)
  - [Custom collection item classes](#Custom-collection-item-classes)
  - [HTML Template Example](#HTML-Template-Example)
- [Management Commands](#Management-Commands)
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
    "paper_uploads",
    # ...
]
```

Configure `paper-uploads` in django's `settings.py`:
```python
PAPER_UPLOADS = {
    "VARIATION_DEFAULTS": {
        "jpeg": dict(
            quality=80,
            progressive=True,
        ),
        "webp": dict(
            quality=75,
        )
    }
}

# Add JS translations
PAPER_LOCALE_PACKAGES = [
   "paper_admin",
   "paper_uploads",
   "django.contrib.admin",
]
```

## FileField

Поле для загрузки файла. В большинстве случаев это поле можно использовать
вместо одноименного поля Django.

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import FileField


class Page(models.Model):
    report = FileField(
        _("file"), 
        blank=True
    )
```

Результат с загруженным файлом:
![image](https://user-images.githubusercontent.com/6928240/152319447-5d7e9a60-5362-4019-bddc-2f2672a6c9cf.png)

На загружаемые файлы можно наложить ограничения с помощью валидаторов.

## Validators

Модуль `paper-uploads.validators` предоставляет следующие классы для валидации файлов:

* `MaxSizeValidator` - задает максимально допустимый размер файла.
  <br>Максимальный размер можно указать как в виде числа (в байтах), 
  так и в виде строки.
  <br>Например: `4 * 10 ** 6`, `4mb`, `4MB`, `4M`.
* `ExtensionValidator` - задает допустимые расширения файлов.
* `MimeTypeValidator` - задает допустимые MIME-типы файлов.
* `ImageMinSizeValidator` - устанавливает минимальный размер загружаемых изображений.
* `ImageMaxSizeValidator` - устанавливает максимальный размер загружаемых изображений.

Пример:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import FileField
from paper_uploads.validators import ExtensionValidator, MaxSizeValidator


class Page(models.Model):
    report = FileField(
        _("file"), 
        blank=True,
        validators=[
            ExtensionValidator([".pdf", ".doc", ".docx"]),
            MaxSizeValidator("10MB")
        ]
    )
```

Ограничения, наложенные этими валидаторами, отображаются в виджете: 
![image](https://user-images.githubusercontent.com/6928240/152322863-33108ef9-061c-4af5-8d0c-aeb5b467e04b.png)

## UploadedFile

Файл, загруженный в поле `FileField`, будет представлен экземпляром модели `UploadedFile`.
Помимо ссылки на файл, эта модель включает множество дополнительных полей:

| Поле | Описание |
|------|----------|
| display_name | Удобочитаемое название файла для вывода на сайте.<br>Заполняется в диалоговом окне редактирования файла.<br>Пример: `Annual report 2020`. |
| basename | Имя файла без пути, суффикса и расширения.<br>Пример: `report2020`. |
| extension | Расширение файла в нижнем регистре без точки.<br>Пример: `pdf`. |
| name | Полное имя файла, хранящееся в БД.<br>Пример: `files/report2020_19sc2Kj.pdf`. |
| size | Размер файла в байтах. |
| checksum | Контрольная сумма файла.<br>Используется для отслеживания изменений файла. |
| uploaded_at | Дата и время загрузки файла. |
| created_at | Дата и время создания экземпляра модели. |
| modified_at | Дата и время изменения экземпляра модели. |

Большинство этих полей заполняется автоматически при загрузке файла.
Поле `display_name` можно заполнить в диалоговом окне редактирования файла.

![image](https://user-images.githubusercontent.com/6928240/152342756-9ccf2579-7c47-4627-9504-8e6fc7b4eecf.png)

Несмотря на то, что фактическая ссылка на файл расположена в поле `Page.report.file`,
для непосредственной работы с файлом на диске во многих случаях можно использовать `Page.report`,
поскольку многие методы и свойства стандартного класса `FieldFile` проксированы на уровень модели. 
В их числе:
* `url`
* `path`
* `open`
* `close`
* `closed`
* `read`
* `seek`
* `tell`
* `chunks`

Поддерживается протокол контекстного менеджера:
```python
page = Page.objects.first()

with page.report.open() as fp:
    print(fp.read(10))
```

## Programmatically upload files

```python
from paper_uploads.models import *

report = UploadedFile()
report.set_owner_field(Page, "report")
report.attach("/tmp/file.doc")
report.save()

page = Page.objects.create(
    report=report
)
```

В метод `set_owner_field()` передаётся модель и имя поля этой модели, в которое
будет сохранен экземпляр модели файла. Эти данные необходимы для выявления
файлов, которые нигде не используются.

Метод `attach()` произодит непосредственное сохранение файла и заполняет объект
дополнительными данными о файле. В метод можно передать как путь к файлу, 
так и файловый объект.

## ImageField

Поле для загрузки изображений. Может хранить ссылку как на единственное изображение 
(подобно стандартному полю `ImageField`), так и на группу изображений,
полученных из исходного с помощью библиотеки [variations][variations]. 

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import *


class Page(models.Model):
    image = ImageField(
        _("single image"), 
        blank=True
    )
    image_group = ImageField(
        _("image group"), 
        blank=True,
        variations=dict(
            desktop=dict(
                size=(1200, 0),
                clip=False
            ),
            mobile=dict(
                size=(600, 0),
                clip=False
            ),
        )
    )
```

При загрузке изображения создается экземпляр модели `UploadedImage`.

## UploadedImage

Модель изображения `UploadedImage` отличается от модели файла `UploadedFile` тем, 
что в ней отстутсвует поле `display_name`, но присутствует несколько специфических полей:

| Поле | Описание |
|------|----------|
| title | Название изображения, которое можно вставить в атрибут `title` тэга `<img>`. |
| description | Описание изображения, которое можно вставить в атрибут `alt` тэга `<img>`. |
| width | Ширина загруженного изображения. |
| height | Высота загруженного изображения. |
| basename | Имя файла без пути, суффикса и расширения.<br>Пример: `photo`. |
| extension | Расширение файла в нижнем регистре без точки.<br>Пример: `jpg`. |
| name | Полное имя файла, хранящееся в БД.<br>Пример: `images/photo_19sc2Kj.jpg`. |
| size | Размер файла в байтах. |
| checksum | Контрольная сумма файла.<br>Используется для отслеживания изменений файла. |
| uploaded_at | Дата и время загрузки файла. |
| created_at | Дата и время создания экземпляра модели. |
| modified_at | Дата и время изменения экземпляра модели. |

Если для изображения заданы вариации, доступ к ним можно получить через экземпляр 
`UploadedImage`, используя имена вариаций: 

```html
<img src="{{ page.image_group.url }}"
     srcset="{{ page.image_group.desktop.url }} 1200w, {{ page.image_group.mobile.url }} 600px"
     sizes="100vw"
     width="{{ page.image_group.width }}"
     height="{{ page.image_group.height }}"
     alt="{{ page.image_group.description }}">
```

### Variations

Вариация - это изображение, полученное из исходного по *заранее* объявленным правилам.

Создание файлов вариаций происходит в момент загрузки изображения на сервер. Поэтому изменение
настроек вариаций не окажет никакого эффекта на уже загруженные изображения.

Для того, чтобы создать файлы для новых вариаций (либо перезаписать существующие файлы 
вариаций, в которые были внесены изменения) можно поступить одним из ниже описанных способов.

1. Вызвать метод `recut()` (либо `recut_async()`) из экземпляра 
   `UploadedImage`:

   ```python
   page.image_group.recut()
   ```
   
   При вызове этого метода все файлы вариаций для указанного экземпляра 
   создаются заново.
   <br>
   <br>
   Можно явно указать имена вариаций, которые необходимо перезаписать:
   ```python
   page.image_group.recut(["desktop", "mobile"]) 
   ```

2. Выполнить management-команду `recreate_variations`:
   ```shell
   python3 manage.py recreate_variations app.page \ 
           --field image_group
           --variations desktop mobile
   ```

   Эта команда сгенерирует вариации для всех экземпляров указанной модели.

#### Versions

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
from django.utils.translation import gettext_lazy as _
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
from django.utils.translation import gettext_lazy as _
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

### Redis Queue

При загрузке большого количества изображений процесс создания вариаций может занимать 
значительное время. Эту работу можно вынести в отдельный процесс с помощью 
[django-rq][django-rq]:

```shell
pip install django-rq
```

```python
# settings.py
PAPER_UPLOADS = {
    "RQ_ENABLED": True,
    "RQ_QUEUE_NAME": "default",
    # ...
}
```

Теперь при загрузке изображений, в очередь под именем `default` будет добавляться
задача, которая создаст все необходимые вариации.

## Collections

Коллекция — это модель, группирующая экземпляры других моделей (элементов коллекции). 
В частности, с помощью коллекции можно создать фото-галерею или список файлов.

Для создания коллекции необходимо объявить класс, унаследованный от `Collection` 
и указать модели элементов, которые могут входить в коллекцию с помощью псевдо-поля 
`CollectionItem`:

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

Класс `Collection` обладает особенным свойством: *любой дочерний класс, унаследованный 
от `Collection`, является proxy-моделью для `Collection`*.

В большинстве случаев коллекции отличаются друг от друга только набором элементов, 
которые могут входить в коллекцию. Использование proxy-моделей предотвращает создание 
множества одинаковых таблиц в БД.

Если же для коллекции необходима отдельная таблица (например, если вы решили добавить 
в неё новое поле), то необходимо явно установить свойство `Meta.proxy` в значение `False`:

```python
from django.db import models
from paper_uploads.models import *


class CustomCollection(Collection):
    name = models.CharField("name", max_length=128, blank=True)

    file = CollectionItem(FileItem)

    class Meta:
        proxy = False
```

### Collection items

Псевдо-поле `CollectionItem` регистрирует модель элемента коллекции под заданным именем. 

```python
from paper_uploads.models import *


class PageFiles(Collection):
    svg = CollectionItem(SVGItem)
    image = CollectionItem(ImageItem)
    file = CollectionItem(FileItem)
```

В приведённом примере, коллекция `PageFiles` может включать элементы трех моделей: 
`SVGItem`, `ImageItem` и `FileItem`. 

Порядок объявления элементов коллекции важен: первый класс модели, чей метод `accept()` 
вернет `True`, определит модель загруженного файла. По этой причине *`FileItem` должен 
указываться последним*, т.к. он принимает любые файлы.

Получить элементы определённого типа можно с помощью метода `get_items()`:
```python
for item in page.files.get_items("image"):
    # ...
```

---

В состав библиотеки входят следующие модели элементов:
* `ImageItem`<br>
  Для хранения изображения с возможностью нарезки на [вариации](#Variations). 
  Допускются тоьлко те файлы, которые можно открыть с помощью [Pillow](https://pillow.readthedocs.io/en/stable/). 

* `SVGItem`<br>
  Для хранения SVG иконок.

* `FileItem`<br>
  Может хранить любой файл.
  
Вариации для изображений коллекции можно указать двумя способами:
1) В дополнительных параметрах поля `CollectionItem` по ключу `variations`:

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
2) В атрибуте класса коллекции `VARIATIONS`:

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
            size=(640, 800),
        )
    )
```

### Custom collection item classes

В простейших случаях, вместо создания собственного класса элемента коллекции с нуля,
можно использовать прокси-модели на основе существующих классов. Например, для того, 
чтобы хранить файлы определённой галереи в отдельной папке, можно создать прокси 
модель к `ImageItem`:

```python
from paper_uploads.models import *


class CustomImageItem(ImageItem):
    class Meta:
        proxy = True
        
    def get_file_folder(self) -> str:
        return "custom-images/%Y"


class Gallery(Collection):
    image = CollectionItem(CustomImageItem)
```

Для более сложных случаев (когда требуется отдельная таблица в БД) необходимо 
использовать прямое наследование. Но уже не от конкретных моделей (`FileItem`, 
`ImageItem` и т.п.), а от абстрактных &mdash; `FileItemBase`, `ImageItemBase`, 
`SVGItemBase`. Или ещё более общих: `CollectionItemBase` и `CollectionFileItemBase`.

```python
from django.db import models
from paper_uploads.models import *


class CustomImageItem(ImageItemBase):  # наследование не от ImageItem!
    caption = models.TextField("caption", blank=True)


class CustomCollection(Collection):
    image = CollectionItem(CustomImageItem)
```

### HTML Template Example

```html
{% if page.gallery %}
<div class="gallery">
  {% for item in page.gallery %}
  
    {% if item.type == "image" %}
      <div class="item item--{{ item.type }}">
        <img src="{{ item.url }}" 
             width="{{ item.width }}"
             height="{{ item.height }}"
             title="{{ item.title }}"
             alt="{{ item.description }}">
      </div>
    {% elif item.type == "file" %}}
      <div class="item item--{{ item.type }}">
        <a href="{{ item.url }}" download>
          Download file "{{ item.display_name }}" ({{ item.size|filesizeformat }})
        </a>
      </div>
    {% endif %}}
  
  {% endfor %}
</div>
{% endif %}
```

### Programmatically create collection item

```python
from django.db import models
from paper_uploads.models import *


class PageGallery(ImageCollection):
    pass


class Page(models.Model):
    gallery = CollectionField(PageGallery)


gallery = PageGallery()
gallery.set_owner_field(Page, "gallery")
gallery.save()

item = ImageItem()
item.attach("/tmp/image.jpg")
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
* у элементов коллекций указано корректное значение а поле `type`
* модель элемента коллекции идентична модели, указанной в классе коллекции

При указании ключа `--fix-missing-variations` все отсутствующие
вариации изображений будут автоматически перенарезаны
из исходников.

```shell
python3 manage.py check_uploads --fix-missing-variations
```

#### clean_uploads
Находит мусорные записи в БД (например те, у которых
нет владельца) и предлагает их удалить.

Владелец загруженного файла устанавливается в момент сохранения страницы
в админке. Это происходит позже фактической загрузки файла на сервер. 
Как следствие, в течение некоторого времени файл будет являться "сиротой". 
Для того, чтобы такие файлы не удалялись, команда `clean_uploads` игнорирует
файлы, загруженные за последние 60 минут. Изменить интервал фильтрации
можно через ключ `--min-age`.

```shell
python3 manage.py clean_uploads --min-age=1800
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

### `COLLECTION_ITEM_PREVIEW_WIDTH`, `COLLECTION_ITEM_PREVIEW_HEIGHT`
Размеры превью элементов коллекций в админке.

Значение по умолчанию: `180` x `135`

### `COLLECTION_IMAGE_ITEM_PREVIEW_VARIATIONS`
Вариации, добавляемые к каждому классу изображений коллекций
для отображения превью в админке. Размеры файлов должны
совпадать с `COLLECTION_ITEM_PREVIEW_WIDTH` и
`COLLECTION_ITEM_PREVIEW_HEIGHT`.

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
