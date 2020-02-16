"""
Specific settings for CI run
"""
from .test_settings import *  # pylint: disable=unused-wildcard-import,wildcard-import;  # noqa: F401,F403

HEADLESS_TEST_MODE = True


# Disable E-Mail completely
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
