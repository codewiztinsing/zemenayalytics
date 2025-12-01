import os
from pathlib import Path
from config.settings import get_secret
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Get SECRET_KEY from environment, with a fallback for development
SECRET_KEY = get_secret(
    "SECRET_KEY",
    backup="django-insecure-dev-key-change-in-production-q+j44lxsbytpqrafkwq_gr(5d4fsc%ohiwff3%624gqvo=o2m1"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "drf_spectacular",
    "django_celery_beat",
    # Local apps
    "apps.analytics",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (User uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework configuration
# Pagination settings from environment variables
API_PAGE_SIZE = int(get_secret("API_PAGE_SIZE", backup=100))
API_MAX_PAGE_SIZE = int(get_secret("API_MAX_PAGE_SIZE", backup=1000))

REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "VERSION_PARAM": "version",
    "DEFAULT_PAGINATION_CLASS": "apps.analytics.pagination.ConfigurablePageNumberPagination",
    "PAGE_SIZE": API_PAGE_SIZE,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Zemenay Analytics API",
    "DESCRIPTION": "Analytics API for blog views, top analytics, and performance metrics",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # SCHEMA_PATH_PREFIX removed - using postprocessing hook to handle /api/ and /api/v1/ removal
    "POSTPROCESSING_HOOKS": [
        "apps.analytics.api.hooks.remove_api_prefixes_from_paths",
        "apps.analytics.api.hooks.remove_schemas_from_components",
    ],
    "TAGS": [
        {"name": "Analytics", "description": "Analytics endpoints for blog views and performance metrics"},
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    # Hide schemas section in Swagger UI
    # Note: We keep schemas in the document for reference resolution
    # but hide them in the UI with defaultModelsExpandDepth: -1
    "SWAGGER_UI_SETTINGS": {
        "defaultModelsExpandDepth": -1,  # Completely hide schemas section
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
}

# Logging configuration with colored output (if colorlog is available)
# Check if colorlog is available
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

# Build formatters based on colorlog availability
formatters = {
    "verbose": {
        "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
        "style": "{",
    },
    "simple": {
        "format": "{levelname} {message}",
        "style": "{",
    },
}

if COLORLOG_AVAILABLE:
    formatters["colored"] = {
        "()": "colorlog.ColoredFormatter",
        "format": "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s %(message)s",
        "log_colors": {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    }
    console_formatter = "colored"
else:
    # Fallback formatter with level names for visibility
    formatters["standard"] = {
        "format": "{levelname:8s} {name} {message}",
        "style": "{",
    }
    console_formatter = "standard"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": formatters,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": console_formatter,
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = BASE_DIR / "logs"
os.makedirs(logs_dir, exist_ok=True)

# Celery Configuration
CELERY_BROKER_URL = get_secret("CELERY_BROKER_URL", backup="redis://redis:6379/0")
CELERY_RESULT_BACKEND = get_secret("CELERY_RESULT_BACKEND", backup="redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat Configuration
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
