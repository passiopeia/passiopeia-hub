"""
Template Tags for language handling
"""

from django import template
from django.utils import translation

register = template.Library()  # pylint: disable=invalid-name


@register.simple_tag(name='current_language')
def do_current_language() -> str:
    """
    Get the current language code

    :rtype: str
    :returns: The current language code
    """
    return translation.get_language()
