"""
Models supporting "my account"
"""
from uuid import uuid4

from django.db.models import Model, UUIDField, OneToOneField, CASCADE, DateTimeField, CharField, EmailField
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from hub_app.accountlib.email import get_email_max_validity, get_email_key
from hub_app.models.users import HubUser


class PendingEMailChange(Model):
    """
    Keep Information about an E-Mail-Change
    """

    class Meta:
        verbose_name = _('Pending E-Mail Change')
        verbose_name_plural = _('Pending E-Mail Changes')
        default_permissions = ('add', 'change', 'delete')
        permissions = ()

    uuid = UUIDField(_('UUID'), primary_key=True, blank=False, null=False, default=uuid4)
    user = OneToOneField(HubUser, unique=True, verbose_name=_('User'), blank=False, null=False, on_delete=CASCADE)
    new_email = EmailField(null=False, blank=False)
    created = DateTimeField(_('Created'), blank=False, null=False, default=now)
    valid_until = DateTimeField(_('Valid Until'), blank=False, null=False, default=get_email_max_validity)
    key = CharField(_('E_Mail Change Key'), max_length=255, blank=False, null=False, default=get_email_key)

    def __str__(self):
        return '{} ({})'.format(str(self.uuid), self.user.username)
