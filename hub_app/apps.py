"""
Django Application config
"""
from django.apps import AppConfig

from django.utils.translation import gettext_lazy as _


class HubAppConfig(AppConfig):
    """
    App Config for the 'hub_app'
    """
    name = 'hub_app'
    verbose_name = _('* Passiopeia Hub')
