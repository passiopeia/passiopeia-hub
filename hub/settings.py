"""
Django settings for hub project.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

from django.contrib import messages
from django.urls import reverse_lazy

from django.utils.translation import gettext_lazy as _


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'NEVER_USE_THIS_IN_PRODUCTION_00000000000000000000000000000000000000000000000'  # nosec

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'hub_app',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

ROOT_URLCONF = 'hub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'hub.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# User Model and Auth Backend
AUTH_USER_MODEL = 'hub_app.HubUser'
AUTHENTICATION_BACKENDS = (
    'hub_app.authlib.backend.TotpAuthenticationBackend',
)


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', 'English'),
    ('de', 'Deutsch'),
)

TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '_compiled_static_files')


# CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = CSP_DEFAULT_SRC
CSP_IMG_SRC = CSP_DEFAULT_SRC
CSP_OBJECT_SRC = CSP_DEFAULT_SRC
CSP_MEDIA_SRC = CSP_DEFAULT_SRC
CSP_FRAME_SRC = CSP_DEFAULT_SRC
CSP_FONT_SRC = CSP_DEFAULT_SRC
CSP_CONNECT_SRC = CSP_DEFAULT_SRC
CSP_STYLE_SRC = CSP_DEFAULT_SRC
CSP_FORM_ACTION = CSP_DEFAULT_SRC
CSP_MANIFEST_SRC = CSP_DEFAULT_SRC
CSP_WORKER_SRC = CSP_DEFAULT_SRC


# Language Cookie settings
LANGUAGE_COOKIE_NAME = 'passiopeia_hub_language'
LANGUAGE_COOKIE_AGE = None
LANGUAGE_COOKIE_HTTPONLY = True
LANGUAGE_COOKIE_SECURE = True
LANGUAGE_COOKIE_SAMESITE = 'Strict'


# CSRF Cookie settings
CSRF_COOKIE_NAME = 'passiopeia_hub_csrf'
CSRF_COOKIE_AGE = None
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True


# Session Cookie Settings
SESSION_COOKIE_NAME = 'passiopeia_hub_session'
SESSION_COOKIE_AGE = 24 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# Settings for the test subsystem
HEADLESS_TEST_MODE = True


# Locale Settings
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)


# Upload Handling
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

MAX_UPLOAD_SIZE = 5242880


# Additional Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'


# Login Settings
LOGIN_URL = reverse_lazy('ha:auth:login')
LOGOUT_URL = reverse_lazy('ha:auth:logout')
LOGIN_REDIRECT_URL = reverse_lazy('ha:home')
LOGOUT_REDIRECT_URL = reverse_lazy('ha:home')
REGISTER_URL = reverse_lazy('ha:reg:step.1')
MY_ACCOUNT_URL = '#'


# E-Mail Settings
EMAIL_REGISTRATION_FROM = 'registration.no-reply@passiopeia.github.io'
EMAIL_REGISTRATION_SUBJECT = _('[Passiopeia Hub] Registration: Please confirm your registration')
EMAIL_SUBJECT_PREFIX = '[Passiopeia Hub] '
EMAIL_USE_LOCALTIME = False
# Other E-Mail Settings: https://docs.djangoproject.com/en/3.0/ref/settings/#email-host


# Notifications
ADMINS = (
    ('Test Admin', 'test-admin@passiopeia.github.io'),
)
