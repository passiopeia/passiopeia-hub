"""
Work with registration keys
"""
from random import SystemRandom
from string import ascii_letters, digits


def get_registration_key() -> str:
    """
    Get a Registration Key
    """
    random = SystemRandom()
    return ''.join(random.choices(ascii_letters + digits + '-_.~', k=250))
