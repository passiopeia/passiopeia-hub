"""
Validate OTP
"""
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class OtpValidator(RegexValidator):  # pylint: disable=too-few-public-methods
    """
    Simple OTP Validation based on Regex Validator
    """

    def __init__(self):
        super().__init__(r'^[0-9]{6}$', _('Only numbers allowed.'))
