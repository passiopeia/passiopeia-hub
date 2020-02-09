"""
Template Tags for language handling
"""
from uuid import uuid4

from django import template
from django.template import RequestContext
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


@register.inclusion_tag('hub_app/inclusion/language-selector.html', name='language_selector', takes_context=True)
def do_language_selector(context: RequestContext) -> dict:
    """
    Just fills the context for the template
    """
    return {
        'rqc': context,
        'instance': str(uuid4())
    }
