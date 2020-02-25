"""
Template Tag for putting the admin switch in templates
"""
from uuid import uuid4

from django import template
from django.template import RequestContext
from django.urls import reverse_lazy

register = template.Library()  # pylint: disable=invalid-name


@register.inclusion_tag('hub_app/inclusion/admin-switch.html', name='admin_switch', takes_context=True)
def do_admin_switch(context: RequestContext) -> dict:
    """
    Prepare the context for the template tag
    """
    user = getattr(context.request, 'user', None)
    render = user is not None and user.is_staff
    return {
        'instance': uuid4(),
        'render': render,
        'admin_link': reverse_lazy('admin:index'),
    }
