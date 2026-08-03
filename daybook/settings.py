import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-daybook-change-this-in-production-abc123xyz'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tasks',
    'reports',
    'habits',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'daybook.middleware.NoCacheMiddleware',
]

ROOT_URLCONF = 'daybook.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'habits.context_processors.user_preferences',
            ],
        },
    },
]

WSGI_APPLICATION = 'daybook.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Needed for UserSettings.avatar (habits app, Phase 0). Upload UI itself is
# Phase 8 — this just makes the field usable once that's built.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'

# ─── Phase 9: Daily Report email ────────────────────────────────────────────
# All real credentials come from environment variables — never hardcode an
# SMTP password in this file. With none set, EMAIL_BACKEND defaults to the
# console backend, which just prints emails to the terminal instead of
# sending them — safe out of the box for local development.
EMAIL_BACKEND = os.environ.get('DAYBOOK_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('DAYBOOK_EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('DAYBOOK_EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('DAYBOOK_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('DAYBOOK_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('DAYBOOK_EMAIL_USE_TLS', 'true').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DAYBOOK_DEFAULT_FROM_EMAIL', 'noreply@daybook.local')

# Set DAYBOOK_ENABLE_SCHEDULER=1 to have the app start its own in-process
# background scheduler (habits/scheduler.py) on startup. Left off by
# default — see the scheduler module's docstring and the phase writeup for
# why this needs a deliberate decision, not an automatic default.