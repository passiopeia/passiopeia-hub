"""
Template Tag for Handling the Login links/dropdowns in templates
"""
from uuid import uuid4

from django import template
from django.conf import settings
from django.template import RequestContext

register = template.Library()  # pylint: disable=invalid-name


@register.inclusion_tag('hub_app/inclusion/login-menu.html', name='login_menu', takes_context=True)
def do_login_menu(context: RequestContext) -> dict:
    """
    Just fills the context for the template
    """
    user = getattr(context.request, 'user', None)
    return {
        'user': user,
        'instance': str(uuid4()),
        'logout_url': settings.LOGOUT_URL,
        'login_url': settings.LOGIN_URL,
        'register_url': settings.REGISTER_URL,
        'account_url': settings.MY_ACCOUNT_URL,
        'next_url': context.request.get_full_path(),
    }
