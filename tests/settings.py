import os

from django.utils.translation import ugettext_lazy as _
from dotenv import load_dotenv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's3296tl(k324sma5wez=vyvta+w4!%ez3^nlj#hh5bn=n!i+gr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'paper_admin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'paper_uploads',
    'paper_uploads.cloudinary',
    'django_rq',
    'django_jinja',
    'cloudinary',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'NAME': 'django',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
    {
        'NAME': 'jinja2',
        'BACKEND': 'django_jinja.backend.Jinja2',
    }
]

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'static'))

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'media'))
FILE_UPLOAD_PERMISSIONS = 0o666


# ===========
#  Django RQ
# ===========
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 1,
        'DEFAULT_TIMEOUT': '5m',
    },
}

# =============
#  Paper Admin
# =============
PAPER_ENVIRONMENT_NAME = "development"
PAPER_ENVIRONMENT_COLOR = "#FFFF00"

PAPER_MENU = [
    dict(
        label=_('Dashboard'),
        url='admin:index',
        icon='fa fa-fw fa-lg fa-area-chart',
    ),
    dict(
        app='app',
        icon='fa fa-fw fa-lg fa-home',
    ),
    '-',
    'auth',
]

# ===============
#  Paper Uploads
# ===============
PAPER_UPLOADS = {
    # 'RQ_ENABLED': True,
    'VARIATION_DEFAULTS': {
        'face_detection': True,
        'jpeg': dict(
            quality=80,
            progressive=True,
        ),
        'webp': dict(
            quality=75,
        )
    }
}

PAPER_LOCALE_PACKAGES = [
    "django.contrib.admin",
    "paper_admin",
    "paper_uploads",
]

load_dotenv()
