"""
    ===================
      Загрузка файлов
    ===================

    Каждый загруженный файл представлен моделью, унаследованной от UploadedFileBase.
    Связь любой модели с файлом осуществляется через поля:
        1) FileField        - загрузка файла
        2) ImageField       - загрузка картинки с возможностью нарезки на множество размеров
        3) CollectionField  - загрузка множества картинок и/или файлов
    Все поля являются производными от OneToOneField.
    * Информацию по нарезке картинок смотри в variations.

    Модели файлов проксируют некоторые свойства файла на уровень модели:
        url
        path
        open
        read
        close
        closed
    Таким образом, вместо `Article.image.file.url` можно использовать `Article.image.url`.

    Каждая галерея имеет поле `cover`, ссылающееся на первую картинку из галереи.
    Это сделано для экономии SQL-запросов при выборке множества объектов, имеющих
    галереи. Например, при выводе списка продуктов магазина.

    Есть два класса галереи: Gallery и ImageGallery. ImageGallery позволяет
    загружать только изображения, тогда как в Gallery помимо изображений можно
    добавлять SVG и любые другие файлы.

    Зависит от:
        django-rq (optional)
        variations
        filetype

    Установка
    ---------
    Добавить "paper_uploads" в INSTALLED_APPS:
        INSTALLED_APPS = [
            ...
            'paper_uploads',
        ]

        PAPER_UPLOADS = {
            'STORAGE': 'django.core.files.storage.FileSystemStorage',
            'IMAGES_UPLOAD_TO': 'images/%Y-%m-%d',
            'POSTPROCESS': {
                'JPEG': {
                    'COMMAND': 'jpeg-recompress',
                    'ARGUMENTS': '--quality high --method smallfry {file} {file}',
                }
            }
        }

    Настройки
    ---------
    STORAGE
        type            str
        default         django.core.files.storage.FileSystemStorage
        description     Путь к классу хранилища Django, через который будет
                        осуществляться работа с файлами.

    STORAGE_OPTIONS
        type            dict
        default         {}
        description     Параметры инициализации хранилища, объявленного в STORAGE

    FILES_UPLOAD_TO
        type            str
        default         files/%Y-%m-%d
        description     Путь к папке, в которую загружаются файлы FileField

    IMAGES_UPLOAD_TO
        type            str
        default         images/%Y-%m-%d
        description     Путь к папке, в которую загружаются файлы ImageField

    GALLERY_FILES_UPLOAD_TO
        type            str
        default         gallery/files/%Y-%m-%d
        description     Путь к папке, в которую загружаются файлы галереи

    GALLERY_IMAGES_UPLOAD_TO
        type            str
        default         gallery/images/%Y-%m-%d
        description     Путь к папке, в которую загружаются картинки галереи

    GALLERY_ITEM_PREVIEW_WIDTH
        type            int
        default         144
        description     Ширина превью элемента галереи в виджете админки

    GALLERY_ITEM_PREVIEW_HEIGHT
        type            int
        default         108
        description     Высота превью элемента галереи в виджете админки

    GALLERY_IMAGE_ITEM_PREVIEW_VARIATIONS
        type            dict
        default         ...
        description     Вариации для превью картинок галереи

    RQ_ENABLED
        type            bool
        default         False
        description     Включает нарезку картинок на размеры через отложенные
                        задачи python-rq

    RQ_QUEUE_NAME
        type            str
        default         default
        description     Название очереди, в которую помещаются задачи по нарезке

    POSTPROCESS
        type            bool
        default         dict
        description     Определяет команды, запускаемые после загрузки файла.
                        Для каждого формата файла можно указать свою команду.
                        Путь к исполняемому файлу передается в ключе COMMAND,
                        а её аргументы в ключе ARGUMENTS.

    Постобработка
    -------------
    После нарезки загруженных картинок, они могут быть обработаны сторонними
    утилитами, выполняющими, например, дополнительное сжатие файлов (mozjpeg,
    pngquant). Для каждого формата изображения можно указать свою команду.

    Можно переопределить команду сжатия для конкретной вариации с помощью
    дополнительных параметров вариации:
        high_quality=dict(
            size=(1600, 0),
            jpeg=dict(
                quality=92,
                postprocess=None   # disable postprocess
            ),
        )
        average=dict(
            size=(640, 480),
            png=dict(
                postprocess=dict(
                    command='pngquant',
                    arguments='--skip-if-larger --force --output {file} {file}'
                )
            ),
        )

    Пример
    ------
    # models.py
        from pilkit import processors
        from paper_uploads.models import ImageGallery
        from paper_uploads.models.fields import FileField, ImageField, CollectionField

        class ArticleGallery(ImageGallery):
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

        class Article(models.Model):
            file = FileField(_('simple file'), blank=True)
            image = ImageField(_('simple image'))
            image_ext = ImageField(_('image with variations'),
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
            gallery = CollectionField(ArticleGallery, verbose_name=_('gallery'))

    # shell
        > article.file.url
        '/media/files/2018-10-09/file.pdf'

        > article.file.size
        232434

        > article.image.width
        1920

        > article.image.title
        'Dreamy Rose image'

        > article.image_ext.normal.url
        '/media/images/2018-10-09/image.normal.jpg'
"""
default_app_config = 'paper_uploads.apps.Config'
