from pathlib import Path
import os
import django
from decouple import config, AutoConfig
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

DJANGO_FORMS_TEMPLATES = Path(django.__file__).resolve().parent / "forms" / "templates"

_auto_config = AutoConfig(search_path=BASE_DIR)

SECRET_KEY = _auto_config('DJANGO_SECRET_KEY', default=None)
if not SECRET_KEY:
    try:
        SECRET_KEY = config('DJANGO_SECRET_KEY')
    except Exception:
        SECRET_KEY = None

if not SECRET_KEY:
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or get_random_secret_key()

DEBUG = _auto_config("DJANGO_DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Локальные приложения
    "projects",
    "users",
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

ROOT_URLCONF = "team_finder.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / f"templates_var{_auto_config('TASK_VERSION', default='1')}",
            DJANGO_FORMS_TEMPLATES,
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "team_finder.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _auto_config("POSTGRES_DB"),
        "USER": _auto_config("POSTGRES_USER"),
        "PASSWORD": _auto_config("POSTGRES_PASSWORD"),
        "HOST": _auto_config("POSTGRES_HOST", default="localhost"),
        "PORT": _auto_config("POSTGRES_PORT", default=5432, cast=int),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []
if not DEBUG:
    AUTH_PASSWORD_VALIDATORS.extend(
        [
            {
                "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
            },
            {
                "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            },
            {
                "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
            },
            {
                "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
            },
        ]
    )

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Media files

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Use custom user model
AUTH_USER_MODEL = "users.User"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
