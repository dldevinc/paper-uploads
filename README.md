# paper-uploads
Асинхронная загрузка файлов для административного интерфейса Django.

[![PyPI](https://img.shields.io/pypi/v/paper-uploads.svg)](https://pypi.org/project/paper-uploads/)
[![Build Status](https://github.com/dldevinc/paper-uploads/actions/workflows/tests.yml/badge.svg)](https://github.com/dldevinc/paper-uploads)
[![Software license](https://img.shields.io/pypi/l/paper-uploads.svg)](https://pypi.org/project/paper-uploads/)

## Requirements
* Python >= 3.6
* Django >= 2.2
* [paper-admin][paper-admin] >= 4.1.0
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

## Table of Contents

- [Installation](#Installation)
- [Описание](#Описание)
- [FileField и ImageField](#FileField-и-ImageField)
  - [Поля моделей загруженных файлов](#Поля-моделей-загруженных-файлов)
  - [Storage](#Storage)
  - [Каталог загрузки файла](#Каталог-загрузки-файла)
  - [Валидаторы](#Валидаторы)
  - [Программная загрузка файлов](#Программная-загрузка-файлов)
  - [Вариации](#Вариации)
    - [Версии вариаций](#Версии-вариаций)
    - [Redis Queue](#Redis Queue)
- [SVGFileField](#SVGFileField)
- [Коллекции](#Коллекции)
  - [Элементы коллекции](#Элементы-коллекции)
    - [Storage и каталог загрузки файлов](#Storage-и-каталог-загрузки-файлов)
    - [Валидаторы](#Валидаторы-2)
    - [Программное создание элемента коллекции](#Программное-создание-элемента-коллекции)
    - [Вариации](#Вариации-2)
  - [HTML Template Example](#HTML-Template-Example)
- [Management команды](#Management-команды)
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

## Описание
В состав библиотеки входит два поля &mdash; `FileField` и `ImageField` &mdash;
и модель `Collection`, предназначенная для группировки загруженных файлов
с целью создания, к примеру, фотогалерей.

С примерами использования библиотеки вы можете ознакомиться 
[здесь](https://github.com/dldevinc/paper-uploads/tree/master/tests/examples).

## FileField и ImageField

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import FileField, ImageField


class Page(models.Model):
    file = FileField(
        _("file"),
        blank=True
    )
    image = ImageField(
        _("image"),
        blank=True
    )
```

![image](https://user-images.githubusercontent.com/6928240/154901303-be8a6a26-c0c1-4bb1-a9cc-ece14f5b04d2.png)

Эти поля используются для тех же целей, что и одноимённые стандартные поля Django
&mdash; для загрузки файлов и изображений &mdash; но имеют ряд существенных отличий. 

Главное отличие заключается в том, что поля `FileField` и `ImageField` являются 
производными от стандартного `OneToOneField`. Соответственно, загруженные файлы
представлены экземплярами полноценных моделей. 

### Поля моделей загруженных файлов

Файлы, загруженные с помощью полей `FileField` и `ImageField`, хранятся в
экземплярах моделей `UploadedFile` и `UploadedImage` соответственно.

В следующих таблицах перечислены общие поля и свойства обеих моделей:

| Поле | Описание |
|------|----------|
| resource_name | Имя файла без пути, суффикса и расширения.<br>Пример: `report2020`. |
| extension | Расширение файла в нижнем регистре без точки.<br>Пример: `pdf`. |
| size | Размер файла в байтах. |
| checksum | Контрольная сумма содержимого файла.<br>Используется для отслеживания изменений файла. |
| uploaded_at | Дата и время загрузки файла. |
| created_at | Дата и время создания экземпляра модели. |
| modified_at | Дата и время изменения экземпляра модели. |


| Свойство | Описание |
|------|----------|
| name | Полное имя файла.<br>Пример: `files/report2020_19sc2Kj.pdf`. |
| url | URL-адрес файла.<br>Пример: `/media/files/report2020_19sc2Kj.pdf`. |
| path | Абсолютный путь к файлу.<br>Пример: `/home/www/django/media/files/report2020_19sc2Kj.pdf`. |

Ниже перечислены поля и свойства, специфичные для каждой модели.

Специфичные поля `UploadedFile`:

| Поле | Описание |
|------|----------|
| display_name | Удобочитаемое название файла для вывода на сайте.<br>Заполняется в диалоговом окне редактирования файла.<br>Пример: `Annual report 2020`. |

Специфичные поля `UploadedImage`:

| Поле | Описание |
|------|----------|
| title | Название изображения, которое можно вставить в атрибут `title` тэга `<img>`. |
| description | Описание изображения, которое можно вставить в атрибут `alt` тэга `<img>`. |
| width | Ширина загруженного изображения. |
| height | Высота загруженного изображения. |


Большинство полей заполняются автоматически при загрузке файла и предназначены
только для чтения. Но такие поля, как `display_name` или `title`, заполняются
пользователем в диалоговом окне редактирования файла:

![image](https://user-images.githubusercontent.com/6928240/154904780-5d365952-ce75-4491-952e-6b2992e35309.png)
![image](https://user-images.githubusercontent.com/6928240/154910567-991bc27c-e7c6-40e7-883e-f3120897c197.png)

### Storage

По умолчанию все поля `paper-uploads` используют единый экземпляр хранилища,
определяемый настройками `STORAGE` и `STORAGE_OPTIONS`:

```python
# settings.py

PAPER_UPLOADS = {
    "STORAGE": "django.core.files.storage.FileSystemStorage",
    "STORAGE_OPTIONS": {},
    # ...
}
```

Вы можете указать экземпляр хранилища для конкретного поля:

```python
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import FileField


class Page(models.Model):
    report = FileField(
        _("report"), 
        blank=True,
        storage=FileSystemStorage(location="uploads/"),
        upload_to="reports/%Y/%m"
    )
```

### Каталог загрузки файла

Все поля используют единые значения, указанные в настройках 
`FILES_UPLOAD_TO` и `IMAGES_UPLOAD_TO`:

```python
# settings.py

PAPER_UPLOADS = {
    # ...
    "FILES_UPLOAD_TO": "files/%Y/%m/%d",
    "IMAGES_UPLOAD_TO": "images/%Y/%m/%d",
    # ...
}
```

Для конкретного поля каталог сохранения можно указать в параметре поля `upload_to`. 
Параметр поддерживает форматирование `strftime()`, которое будет заменено на 
дату/время загруженного файла (и загружаемые файлы не заполнят один каталог).   

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import FileField


class Page(models.Model):
    report = FileField(
        _("report"), 
        blank=True,
        upload_to="pdf/reports/%Y"
    )
```

Обратите внимание, что в параметр `upload_to` *нельзя передать вызываемый объект*.

Если вам требуется динамическое определение каталога или имени загруженного файла,
создайте proxy-модель и переопрелите метод `generate_filename()`:

```python
import os
import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import FileField, UploadedFile


class UploadedFileProxy(UploadedFile):
    class Meta:
        proxy = True

    def generate_filename(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        filename = "proxy-files/file-%Y-%m-%d_%H%M%S{}".format(ext)
        filename = datetime.datetime.now().strftime(filename)

        storage = self.get_file_storage()
        return storage.generate_filename(filename)


class Page(models.Model):
    file = FileField(
        _("file"),
        to=UploadedFileProxy,
        blank=True,
    )
```

### Валидаторы

На загружаемые файлы можно наложить ограничения с помощью валидаторов.

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

### Программная загрузка файлов

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

В метод `set_owner_field()` передаётся модель и имя поля модели, в которое будет 
сохранен экземпляр модели файла. Эти данные необходимы для выявления файлов, которые 
нигде не используются.

Метод `attach()` производит непосредственное сохранение файла и заполняет экземпляр 
дополнительными данными. В метод можно передать как путь к локальному файлу, так 
и файловый объект.

### Вариации

`ImageField` позволяет создавать вариации для загруженного изображения.
Вариация - это изображение, полученное из исходного по *заранее* объявленным правилам.

Для создания вариаций используется библиотека [variations][variations].

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import *


class Page(models.Model):
    image = ImageField(
        _("image"), 
        blank=True,
        variations=dict(
            desktop=dict(
                size=(800, 0),
                clip=False,
            ),
            mobile=dict(
                size=(600, 0),
                clip=False,
            ),
        )
    )
```

К файлам вариаций можно обратиться через модель `UploadedImage` используя их имена:
```python
print(page.image.desktop.url)
# /media/images/2022/02/21/sample.desktop.jpg
```

Создание файлов вариаций происходит в момент загрузки изображения на сервер. 
Поэтому изменение настроек вариаций не окажет никакого эффекта на уже загруженные 
изображения.

Для того, чтобы создать файлы для новых вариаций (либо перезаписать существующие файлы 
вариаций) можно поступить одним из ниже описанных способов.

1. Вызвать метод `recut()`:

   ```python
   page.image.recut()
   ```
   
   При вызове этого метода все файлы вариаций для текущего экземпляра 
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
           --field image
           --variations desktop mobile
   ```

   Эта команда сгенерирует вариации для всех экземпляров указанной модели.

#### Версии вариаций

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
    image = ImageField(
        _("image"), 
        blank=True,
        variations=dict(
            desktop=dict(
                # ...
                versions={"webp", "2x", "3x"}
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
    image = ImageField(
        _('image'), 
        blank=True,
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

#### Redis Queue

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

## SVGFileField

Поле `SVGFileField` предназначено для загрузки SVG-файлов. Оно идентично `FileField`,
но связанная с ним модель `UploadedSVGFile` включает несколько дополнительных полей:

| Поле | Описание |
|------|----------|
| width | Ширина изображения в формате `Decimal`. Может быть вещественным числом. |
| height | Высота изображения в формате `Decimal`. Может быть вещественным числом. |
| title | Название изображения, которое можно вставить в атрибут `title` тэга `<img>`. |
| description | Описание изображения, которое можно вставить в атрибут `alt` тэга `<img>`. |

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import SVGFileField


class Page(models.Model):
    svg = SVGFileField(
        _("svg"),
        blank=True
    )
```

## Коллекции

Коллекция — это модель, группирующая экземпляры других моделей (элементов коллекции). 
В частности, с помощью коллекции можно создать фотогалерею или список файлов.

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

### Элементы коллекции

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
  Для хранения изображения с возможностью нарезки на [вариации](#Вариации). 
  Допускются только те файлы, которые можно открыть с помощью [Pillow](https://pillow.readthedocs.io/en/stable/). 

* `SVGItem`<br>
  Для хранения SVG иконок.

* `FileItem`<br>
  Может хранить любой файл.

#### Storage и каталог загрузки файлов

По умолчанию элементы коллекции используют тот же экземпляр хранилища,
что используется полями `FileField` и `ImageField`. 

Каталоги загрузки файлов для элементов коллекций указываются в настройках 
`COLLECTION_FILES_UPLOAD_TO` и `COLLECTION_IMAGES_UPLOAD_TO`:

```python
# settings.py

PAPER_UPLOADS = {
    # ...
    "COLLECTION_FILES_UPLOAD_TO": "collections/files/%Y/%m/%d",
    "COLLECTION_IMAGES_UPLOAD_TO": "collections/images/%Y/%m/%d",
    # ...
}
```

Для отдельно взятого элемента коллекции экземпляр хранилища и каталог загрузки  
можно указать в параметре `options` псевдо-поля `CollectionItem`:

```python
from django.core.files.storage import FileSystemStorage
from paper_uploads.models import *


class PageFiles(Collection):
    image = CollectionItem(ImageItem, options={
        "storage": FileSystemStorage(location="uploads/"),
        "upload_to": "gallery",
    })
```

Как в случае с `FileField` и `ImageField`, значением `upload_to` не может выступать 
вызываемый объект. 

Если вам требуется динамическое определение каталога или имени загруженного файла, 
создайте proxy-модель и переопрелите метод `generate_filename()`:

```python
import os
import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import *


class ProxyImageItem(ImageItem):
    class Meta:
        proxy = True

    def generate_filename(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        filename = "gallery/image-%Y-%m-%d_%H%M%S{}".format(ext)
        filename = datetime.datetime.now().strftime(filename)

        storage = self.get_file_storage()
        return storage.generate_filename(filename)


class PageGallery(Collection):
    image = CollectionItem(ProxyImageItem)


class Page(models.Model):
    gallery = CollectionField(
        PageGallery,
        verbose_name=_("gallery")
    )
```

#### <a id="Валидаторы-2" />Валидаторы

На загружаемые в коллекции файлы можно наложить ограничения с помощью валидаторов: 

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from paper_uploads.models import *
from paper_uploads.validators import ImageMaxSizeValidator, ImageMinSizeValidator


class PageGallery(Collection):
    image = CollectionItem(ImageItem, validators=[
        ImageMinSizeValidator(640, 480),
        ImageMaxSizeValidator(4000, 3000)
    ])


class Page(models.Model):
    gallery = CollectionField(
        PageGallery,
        verbose_name=_("gallery")
    )
```

#### Программное создание элемента коллекции

Элементы коллекций создаются почти также, как `UploadedFile` и `UploadedImage`.
Разница лишь в том, что вместо вызова метода `set_owner_field()` необходимо
вызвать метод `attach_to()` для присоединения элемента к коллекции:

```python
from paper_uploads.models import *

collection = PageGallery.objects.create()

item = ImageItem()
item.attach_to(collection)
item.attach("/tmp/image.jpg")
item.save()

page = Page.objects.create(
    gallery=collection
)
```

#### <a id="Вариации-2" />Вариации

Вариации для изображений коллекции можно указать одним из двух способов:

1) Параметр `options` псевдо-поля `CollectionItem`:

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
2) Атрибут класса коллекции `VARIATIONS`:

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

## Management команды

### check_uploads

Запускает комплексную проверку загруженных файлов
и выводит результат.

Список производимых тестов:
* загруженный файл существует
* класс модели владельца (указанный в `owner_app_label` и `owner_model_name`) существует
* в классе модели владельца существует поле, указанное в `owner_fieldname`
* у элементов коллекций указано корректное значение в поле `type`
* модель элемента коллекции соответствует модели, указанной в классе коллекции

```shell
python3 manage.py check_uploads
```

### clean_uploads

Находит мусорные записи в БД (например те, у которых нет владельца) 
и предлагает их удалить.

Владелец загруженного файла устанавливается в момент сохранения страницы
в интерфейсе администратора. Это происходит позже фактической загрузки файла 
на сервер. В промежутке времени между этими событиями файл будет являться "сиротой". 
Для того, чтобы такие файлы не удалялись, команда `clean_uploads` игнорирует
файлы, загруженные в течение последнего часа.

```shell
python3 manage.py clean_uploads
```

### remove_empty_collections

Удаление экземпляров коллекций, в которых нет ни одного элемента.

```shell
python3 manage.py clean_uploads
```

### create_missing_variations

Создаёт отсутствующие файлы вариаций.

```shell
python3 manage.py create_missing_variations
```

### recreate_variations

Создание/перезапись вариаций для всех экземпляров указанной модели.

```shell
# for collections
python3 manage.py recreate_variations --model app.Photos --item-type image

# for regular models
python3 manage.py recreate_variations --model app.Page --field image
```

По умолчанию перенарезаются все возможные вариации для каждого
экземпляра указанной модели. Можно указать конкретные вариации,
которые нужно перенарезать:

```shell
python3 manage.py recreate_variations --model app.Page --field image \
        --variations desktop mobile
```

### remove_variations

Удаление файлов вариаций.
Удаляются только файлы объявленных вариаций.
Параметры аналогичны параметрам `recreate_variations`.

```shell
# for collections
python3 manage.py remove_variations --model app.Photos --item-type image

# for regular models
python3 manage.py remove_variations --model app.Page --field image
```

## Settings

Все настройки указываются в словаре `PAPER_UPLOADS`.

```python
PAPER_UPLOADS = {
    "STORAGE": "django.core.files.storage.FileSystemStorage",
    "STORAGE_OPTIONS": {},
    "FILES_UPLOAD_TO": "files/%Y/%m/%d",
    "IMAGES_UPLOAD_TO": "images/%Y/%m/%d",
    "COLLECTION_FILES_UPLOAD_TO": "collections/files/%Y/%m/%d",
    "COLLECTION_IMAGES_UPLOAD_TO": "collections/images/%Y/%m/%d",
    
    "RQ_ENABLED": True,
    "RQ_QUEUE_NAME": "default",
    
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

Значение по умолчанию: `files/%Y/%m/%d`

### `IMAGES_UPLOAD_TO`
Путь к папке, в которую загружаются файлы из ImageField.

Значение по умолчанию: `images/%Y/%m/%d`

### `COLLECTION_FILES_UPLOAD_TO`
Путь к папке, в которую загружаются файлы коллекций.

Значение по умолчанию: `collections/files/%Y/%m/%d`

### `COLLECTION_IMAGES_UPLOAD_TO`
Путь к папке, в которую загружаются изображения коллекций.

Значение по умолчанию: `collections/images/%Y/%m/%d`

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
вариации &mdash; если только вариация их явно не переопределяет.

Значение по умолчанию: `None`

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

[paper-admin]: https://github.com/dldevinc/paper-admin
[variations]: https://github.com/dldevinc/variations
[pilkit]: https://github.com/matthewwithanm/pilkit
[django-storages]: https://github.com/jschneier/django-storages
[django-rq]: https://github.com/rq/django-rq
