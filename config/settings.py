"""
Django settings for Ride Booking project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _load_dotenv_if_present():
    """
    Lightweight .env loader (no dependency).
    Only sets variables that are not already set in the environment.
    """
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        # If .env is malformed, ignore and rely on real environment variables.
        return


_load_dotenv_if_present()

SECRET_KEY = "django-insecure-@qd@=hh5@0$+i_i+&_uyk1x60zk&)=%kk#t=cx1@fuj8bo#$gn"

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "rides",
    "locations",
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
        "DIRS": [BASE_DIR / "templates"],
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

# MySQL / MariaDB only (XAMPP): create database `ride_booking_db` in phpMyAdmin before migrate.
# Custom engine relaxes Django 6's MariaDB 10.6+ check so XAMPP MariaDB 10.4 works.
DATABASES = {
    "default": {
        "ENGINE": "config.db_backends.mysql",
        "NAME": "ride_booking_db",
        "USER": "root",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "3306",
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home"

# OSM self-hosted services
# Example defaults if you run local containers:
# - Nominatim: http://localhost:8080
# - OSRM:      http://localhost:5000
OSM_NOMINATIM_BASE_URL = os.environ.get("OSM_NOMINATIM_BASE_URL", "http://localhost:8080").rstrip("/")
OSM_OSRM_BASE_URL = os.environ.get("OSM_OSRM_BASE_URL", "http://localhost:5000").rstrip("/")
OSM_HTTP_USER_AGENT = os.environ.get("OSM_HTTP_USER_AGENT", "velora-rides/1.0")
