"""
Template Tag for Handling the Login links/dropdowns in templates
"""
from uuid import uuid4

from django import template
from django.template import RequestContext

register = template.Library()  # pylint: disable=invalid-name


@register.inclusion_tag('hub_app/inclusion/login-menu.html', name='login_menu', takes_context=True)
def do_login_menu(context: RequestContext) -> dict:
    """
    Just fills the context for the template
    """
    return {
        'user_obj': context.request.user,
        'instance': str(uuid4()),
    }
