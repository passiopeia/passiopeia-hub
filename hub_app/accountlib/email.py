"""
Helper for setting up E-Mail
"""
from datetime import timedelta
from random import SystemRandom
from string import ascii_letters, digits

from django.utils.timezone import now


def get_email_key() -> str:
    """
    Get a E-Mail Key
    """
    random = SystemRandom()
    return ''.join(random.choices(ascii_letters + digits + '$=^', k=250))


def get_email_max_validity():
    """
    How long should a E-Mail change request be valid?
    """
    return now() + timedelta(days=1)
