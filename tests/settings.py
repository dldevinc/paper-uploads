import os
import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv
from paper_admin.menu import Item, Divider

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE_DIR))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "s3296tl(k324sma5wez=vyvta+w4!%ez3^nlj#hh5bn=n!i+gr"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "paper_admin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "paper_uploads",
    "django_rq",
    "app",
    "examples.fields.standard",
    "examples.fields.custom_storage",
    "examples.fields.proxy_models",
    "examples.fields.custom_models",
    "examples.fields.validators",
    "examples.collections.standard",
    "examples.collections.custom_storage",
    "examples.collections.proxy_models",
    "examples.collections.custom_models",
    "examples.collections.validators",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "NAME": "django",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            str(BASE_DIR / "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
FILE_UPLOAD_PERMISSIONS = 0o666


# ===========
#  Django RQ
# ===========
RQ_QUEUES = {
    "default": {
        "HOST": "localhost",
        "PORT": 6379,
        "DB": 1,
        "DEFAULT_TIMEOUT": "5m",
    },
}

# =============
#  Paper Admin
# =============
PAPER_ENVIRONMENT_NAME = "development"
PAPER_ENVIRONMENT_COLOR = "#FFFF00"

PAPER_MENU = [
    Item(
        label=_("Dashboard"),
        url="admin:index",
        icon="bi-speedometer",
    ),
    Item(
        app="app",
        icon="bi-house",
    ),
    Item(
        label=_("Examples"),
        icon="bi-house-fill",
        children=[
            Item(
                label=_("File fields"),
                children=[
                    Item(
                        label=_("Standard"),
                        model="standard_fields.Page"
                    ),
                    Item(
                        label=_("Custom Django storage"),
                        model="custom_storage_fields.Page"
                    ),
                    Item(
                        label=_("Proxy models"),
                        model="proxy_models_fields.Page"
                    ),
                    Item(
                        label=_("Custom models"),
                        model="custom_models_fields.Page"
                    ),
                    Item(
                        label=_("Validators"),
                        model="validators_fields.Page"
                    )
                ]
            ),
            Item(
                label=_("Collections"),
                children=[
                    Item(
                        label=_("Standard"),
                        model="standard_collections.Page",
                    ),
                    Item(
                        label=_("Custom Django storage"),
                        model="custom_storage_collections.Page"
                    ),
                    Item(
                        label=_("Proxy models"),
                        model="proxy_models_collections.Page"
                    ),
                    Item(
                        label=_("Custom models"),
                        model="custom_models_collections.Page"
                    ),
                    Item(
                        label=_("Validators"),
                        model="validators_collections.Page"
                    )
                ]
            )
        ]
    ),
    Divider(),
    Item(
        app="auth",
        icon="bi-person-circle",
    )
]

# ===============
#  Paper Uploads
# ===============
PAPER_UPLOADS = {
    # "RQ_ENABLED": True,
    "VARIATION_DEFAULTS": {
        "face_detection": True,
        "jpeg": dict(
            quality=80,
            progressive=True,
        ),
        "webp": dict(
            quality=75,
        )
    }
}

PAPER_LOCALE_PACKAGES = [
    "django.contrib.admin",
    "paper_admin",
    "paper_uploads",
]

DROPBOX_OAUTH2_TOKEN = os.environ["DROPBOX_OAUTH2_TOKEN"]
DROPBOX_ROOT_PATH = os.environ["DROPBOX_ROOT_PATH"]
DROPBOX_WRITE_MODE = os.environ["DROPBOX_WRITE_MODE"]
