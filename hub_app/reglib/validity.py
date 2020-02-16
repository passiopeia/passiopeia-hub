"""
Library for the Registration
"""
from datetime import timedelta

from django.utils.timezone import now


def get_registration_max_validity():
    """
    How long should a registration be valid?
    """
    return now() + timedelta(days=3)
