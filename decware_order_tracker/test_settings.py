"""
Test settings for Decware Order Tracker project.
Uses SQLite for testing to avoid PostgreSQL dependencies.
"""

from .settings import *

# Use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Disable SSL requirement
DATABASES['default']['OPTIONS'] = {}

# Speed up password hashing during tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug for testing
DEBUG = False

# Disable Selenium browser automation during tests
TESTING = True
