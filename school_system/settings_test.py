"""
Configuration de test pour School Management System
"""

from .settings import *

# Base de données de test
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Désactiver les migrations pour les tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Cache en mémoire pour les tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Désactiver les emails pendant les tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Désactiver les logs pendant les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Configuration de test spécifique
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Désactiver la validation des mots de passe pour les tests
AUTH_PASSWORD_VALIDATORS = []

# Configuration des médias pour les tests
MEDIA_ROOT = BASE_DIR / 'test_media'

# Désactiver les middlewares de sécurité pour les tests
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE 
    if not middleware.startswith('django.middleware.security')
]

# Configuration des sessions pour les tests
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
