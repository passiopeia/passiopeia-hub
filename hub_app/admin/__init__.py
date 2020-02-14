"""
Define Admin System
"""
from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session

from django.utils.translation import gettext_lazy as _


class HubAdmin(AdminSite):
    """
    Our own Admin configuration
    """
    site_header = _('Passiopeia Hub Administration')
    site_title = _('Passiopeia Hub Admin')


admin_site = HubAdmin(name='hub_admin')  # pylint: disable=invalid-name

# Django internals
admin_site.register(Group)
admin_site.register(Session)

# Use our login page for admin login
admin_site.login = staff_member_required(admin_site.login, login_url=settings.LOGIN_URL)
