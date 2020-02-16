"""
Validators during registration process
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from hub_app.models import HubUser


def validate_unique_username(value):
    """
    Validate if username is not already taken
    """
    if value is None or not isinstance(value, str):
        raise ValidationError(_('This username is currently not available'))
    username = str(value).strip().lower()
    if len(username) == 0:
        raise ValidationError(_('This username is currently not available'))
    if HubUser.objects.filter(username__iexact=username).exists():
        raise ValidationError(_('"%(value)s" is currently not available'), params={'value': value})
