"""
Specific settings for test run
"""
from .settings import *  # pylint: disable=unused-wildcard-import,wildcard-import;  # noqa: F401,F403

HEADLESS_TEST_MODE = False

LANGUAGE_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False


# Mail delivery to folder
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR, '_e-mail')
