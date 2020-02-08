"""
Template Tags for language handling
"""

from django import template
from django.utils import translation

register = template.Library()


@register.simple_tag(name='current_language')
def do_current_language():
    return translation.get_language()
