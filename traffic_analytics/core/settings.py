"""
Django settings for traffic_analytics project.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/


Created on November 2020 by TucanoRobotics
"""

import os

from pathlib import Path

from core.system import (
    PLACEHOLDER_FOR_SECRET,
    load_env_settings,
)

SERVER_ENV = os.getenv("SERVER_ENV", "DEV").upper()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
SERVE_STATIC = False

# DEFAULT_HOST = "www.diagnosticomadurez4.0.cta.org.co"
# ALLOWED_HOSTS = [DEFAULT_HOST]
DEFAULT_HOST = "207.246.118.54"
ALLOWED_HOSTS = ["207.246.118.54"]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent)
REPO_DIR = str(Path(__file__).resolve().parent.parent.parent)
DJANGO_DIR = str(Path(__file__).resolve().parent.parent)
DATA_DIR = os.path.join(REPO_DIR, "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
TEMPLATES_DIR = os.path.join(DJANGO_DIR, "templates")
STATICFILES_DIR = os.path.join(BASE_DIR, "static")
STATIC_ROOT = os.path.join(DATA_DIR, "static")
MEDIA_ROOT = os.path.join(DATA_DIR, "media")

ENV_DIR = os.path.join(REPO_DIR, "env")
ENV_DEFAULTS_FILE = os.path.join(ENV_DIR, f"{SERVER_ENV.lower()}.env")
ENV_SECRETS_FILE = os.path.join(ENV_DIR, "secrets.env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = PLACEHOLDER_FOR_SECRET
CAPTCHA_SITE_KEY = PLACEHOLDER_FOR_SECRET
CAPTCHA_SECRET_KEY = PLACEHOLDER_FOR_SECRET
MAP_KEY = PLACEHOLDER_FOR_SECRET

LOGIN_URL = "/login"
MEDIA_URL = "/media/"
STATIC_URL = "/static/"

CAPTCHA_SITE_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
MAPBOX_GEOCODING_ENDPOINT = "https://api.mapbox.com/geocoding/v5/mapbox.places/{coords}.json?types=place&country=co&language=es&access_token={token}"

# Page settings
PAGE_DESCRIPTION = "Descubre que tan cerca estás de ser parte de la cuarta revolución industrial realizando un diagnóstico a tu empresa."

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Load Settings Overrides from Environment Config Files
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# settings defined above in this file (settings.py)
SETTINGS_DEFAULTS = load_env_settings(env=globals())

# settings set via env/SERVER_ENV.env
ENV_DEFAULTS = load_env_settings(dotenv_path=ENV_DEFAULTS_FILE, defaults=globals())
globals().update(ENV_DEFAULTS)

# settings set via env/secrets.env
ENV_SECRETS = load_env_settings(dotenv_path=ENV_SECRETS_FILE, defaults=globals())
globals().update(ENV_SECRETS)

# settings set via environemtn variables
ENV_OVERRIDES = load_env_settings(env=dict(os.environ), defaults=globals())
globals().update(ENV_OVERRIDES)


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "core",
    "ui",
    "vehicle_counter",
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

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
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

STATICFILES_DIRS = [STATICFILES_DIR]

ROOT_URLCONF = "core.urls"
AUTH_USER_MODEL = "ui.User"
WSGI_APPLICATION = "core.wsgi.application"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGS_DIR, "django.log"),
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR + "/db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_L10N = True
USE_TZ = True
