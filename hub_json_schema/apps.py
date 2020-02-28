"""
Django Application config
"""
from django.apps import AppConfig

from django.utils.translation import gettext_lazy as _


class HubJsonSchemaConfig(AppConfig):
    """
    App Config for the 'hub_json_schema'
    """
    name = 'hub_json_schema'
    verbose_name = _('* Passiopeia Hub JSON Schema')
