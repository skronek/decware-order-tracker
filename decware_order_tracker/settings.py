"""
Django settings for decware_order_tracker project.

Configuration comes from the environment, or from `.env` locally.
"""

from pathlib import Path
import os
import environ
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

DEBUG = env('DEBUG', default='False') == 'True'

# Production must set SECRET_KEY; only local development may fall back to a default.
SECRET_KEY = env('SECRET_KEY', default='insecure-dev-only-secret-key' if DEBUG else environ.Env.NOTSET)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.herokuapp.com', 'decware-orders.info', 'www.decware-orders.info']
CSRF_TRUSTED_ORIGINS = ['https://decware-orders.info', 'https://www.decware-orders.info']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'orders.apps.OrdersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'decware_order_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'decware_order_tracker/templates')],
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
]

WSGI_APPLICATION = 'decware_order_tracker.wsgi.application'

# From DATABASE_URL (set by Heroku, or in .env locally). Local Postgres has no SSL.
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=not DEBUG),
}

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add the React build directory to the static files dirs
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend', 'build'),
]

# Gzip/Brotli copies without the manifest, which errors on any asset missing from it
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Whitenoise settings
WHITENOISE_ROOT = os.path.join(BASE_DIR, 'staticfiles')
WHITENOISE_INDEX_FILE = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple', # Use a simple formatter for debug output
        },
    },
    'formatters': { # Add a simple formatter
        'simple': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        }
    },
    'loggers': {
        'orders.scraper': { # Target our specific scraper logger
            'handlers': ['console'],
            'level': 'INFO', # Set level to INFO
            'propagate': False,
        },
        'django': { # Keep default Django logging reasonable
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# HTTPS in production: keep the session and CSRF cookies off plain HTTP,
# redirect HTTP to HTTPS and send HSTS (see decware_order_tracker/middleware.py).
# The HTTPS middleware is prepended so it runs outermost.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    MIDDLEWARE = ['decware_order_tracker.middleware.HerokuHttpsMiddleware', *MIDDLEWARE]
