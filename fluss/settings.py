"""
Django settings for elements project.

Generated by 'django-admin startproject' using Django 3.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from pathlib import Path
from omegaconf import omegaconf

conf = omegaconf.OmegaConf.load("config.yaml")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = conf.django.secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = conf.django.debug or False

ALLOWED_HOSTS = conf.django.hosts

STATIC_ROOT = "/var/www/static"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LOK = {
    "PUBLIC_KEY": conf.lok.public_key,
    "KEY_TYPE": conf.lok.key_type,
    "ISSUER": conf.lok.issuer,
}

SUPERUSERS = [
    {
        "USERNAME": conf.django.admin.username,
        "EMAIL": conf.django.admin.email,
        "PASSWORD": conf.django.admin.password,
    }
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "whitenoise.runserver_nostatic",
    "django_filters",
    "taggit",
    "channels",
    "lok",
    "health_check",
    "health_check.db",
    "django_probes",
    "guardian",
    "graphene_django",
    "balder",
    "flow",
    "perms",
    "komment"
]


# S3 Settings


# S3_PUBLIC_DOMAIN = f"{conf.s3.public.host}:{conf.s3.public.port}"  # TODO: FIx
AWS_ACCESS_KEY_ID = conf.minio.access_key
AWS_SECRET_ACCESS_KEY = conf.minio.secret_key
AWS_S3_ENDPOINT_URL = f"{conf.minio.protocol}://{conf.minio.host}:{conf.minio.port}"
# AWS_S3_PUBLIC_ENDPOINT_URL = (
#    f"{conf.minio.public.protocol}://{conf.minio.public.host}:{conf.minio.public.port}"
# )
AWS_S3_URL_PROTOCOL = f"{conf.minio.protocol}:"
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_EXPIRE = 3600


AWS_STORAGE_BUCKET_NAME = conf.minio.buckets[0].name
AWS_DEFAULT_ACL = "private"
AWS_S3_USE_SSL = True
AWS_S3_SECURE_URLS = False  # Should resort to True if using in Production behind TLS
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


HEALTH_CHECK = {
    "DISK_USAGE_MAX": 90,  # percent
    "MEMORY_MIN": 100,  # in MB
}


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "lok.middlewares.request.jwt.JWTTokenMiddleWare",
    "lok.middlewares.request.bouncer.BouncedMiddleware",  # needs to be after JWT and session
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fluss.urls"

CORS_ORIGIN_ALLOW_ALL = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            "templates",
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

WSGI_APPLICATION = "fluss.wsgi.application"
ASGI_APPLICATION = "fluss.asgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": conf.db.engine,
        "NAME": conf.db.db_name,
        "USER": conf.db.username,
        "PASSWORD": conf.db.password,
        "HOST": conf.db.host,
        "PORT": conf.db.port,
    }
}

CHANNEL_LAYERS = {
    "default": {
        # This example app uses the Redis channel layer implementation channels_redis
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(conf.redis.host, conf.redis.port)],
            "prefix": "fluss"
        },
    },
}

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

COMMENTABLE_APPS = ["flow"]
SHARABLE_APPS = ["flow"]

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_USER_MODEL = "lok.LokUser"
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

GRAPHENE = {"SCHEMA": "balder.schema.graphql_schema"}

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            # exact format is not important, this is the minimum information
            "format": "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "console",
            "rich_tracebacks": True,
        },
    },
    "loggers": {
        # root logger
        "": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "oauthlib": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "delt": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "oauth2_provider": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
