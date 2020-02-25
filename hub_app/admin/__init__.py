"""
Define Admin System
"""
from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session

from django.utils.translation import gettext_lazy as _

from hub_app.admin.otp import BurnedOtpAdmin
from hub_app.admin.pending_credential_recovery import PendingCredentialRecoveryAdmin
from hub_app.admin.pending_email_changes import PendingEMailChangeAdmin
from hub_app.admin.pending_registration import PendingRegistrationAdmin
from hub_app.admin.user import HubUserAdmin
from hub_app.models import HubUser, BurnedOtp, PendingRegistration, PendingCredentialRecovery, PendingEMailChange


class HubAdmin(AdminSite):
    """
    Our own Admin configuration
    """
    site_header = _('Passiopeia Hub Administration')
    site_title = _('Passiopeia Hub Admin')


admin_site = HubAdmin(name='hub_admin')  # pylint: disable=invalid-name

# Own Models
admin_site.register(HubUser, HubUserAdmin)
admin_site.register(BurnedOtp, BurnedOtpAdmin)
admin_site.register(PendingRegistration, PendingRegistrationAdmin)
admin_site.register(PendingCredentialRecovery, PendingCredentialRecoveryAdmin)
admin_site.register(PendingEMailChange, PendingEMailChangeAdmin)

# Django internals
admin_site.register(Group)
admin_site.register(Session)

# Use our login page for admin login
admin_site.login = staff_member_required(admin_site.login, login_url=settings.LOGIN_URL)
