"""
Test settings for Decware Order Tracker project.
Uses SQLite for testing to avoid PostgreSQL dependencies.
"""

import os

# settings.py requires SECRET_KEY when DEBUG is off
os.environ.setdefault('SECRET_KEY', 'test-secret-key')

from .settings import *  # noqa: E402

# Use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Speed up password hashing during tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug for testing
DEBUG = False

# Run tests against the production HTTPS setup whatever DEBUG the environment
# (or .env) set when settings.py loaded. The test client sends no
# X-Forwarded-Proto header, so the middleware passes requests through.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
if 'decware_order_tracker.middleware.HerokuHttpsMiddleware' not in MIDDLEWARE:
    MIDDLEWARE = ['decware_order_tracker.middleware.HerokuHttpsMiddleware', *MIDDLEWARE]

# Makes DecwareOrderScraper._init_driver refuse to launch Chrome
TESTING = True
