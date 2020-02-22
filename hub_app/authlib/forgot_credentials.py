"""
Helpers for forgotten credentials
"""
from datetime import timedelta
from random import SystemRandom
from string import ascii_letters, digits

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


RECOVERY_CHOICES = (
    ('username', _('Forgot my Username')),
    ('password', _('Forgot my Password')),
    ('otp-secret', _('Lost my OTP Secret')),
)


def get_recovery_max_validity():
    """
    A request for new credentials is only valid for 1 hour
    """
    return now() + timedelta(hours=1)


def get_recovery_key():
    """
    Get a recovery key
    """
    random = SystemRandom()
    return ''.join(random.choices(ascii_letters + digits + '$/:;,', k=250))
