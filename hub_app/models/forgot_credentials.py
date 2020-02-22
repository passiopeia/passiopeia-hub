"""
Model for Credential Recovery
"""
from uuid import uuid4

from django.db.models import Model, CASCADE, UUIDField, OneToOneField, DateTimeField, CharField
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from hub_app.authlib.forgot_credentials import get_recovery_max_validity, RECOVERY_CHOICES, get_recovery_key
from hub_app.models.users import HubUser


class PendingCredentialRecovery(Model):
    """
    Keep Information about Credential Recovery
    """

    class Meta:
        verbose_name = _('Pending Credential Recovery')
        verbose_name_plural = _('Pending Credential Recoveries')
        default_permissions = ('add', 'change', 'delete')
        permissions = ()

    uuid = UUIDField(_('UUID'), primary_key=True, blank=False, null=False, default=uuid4)
    user = OneToOneField(HubUser, unique=True, verbose_name=_('User'), blank=False, null=False, on_delete=CASCADE)
    recovery_type = CharField(max_length=16, choices=RECOVERY_CHOICES, null=False, blank=False)
    created = DateTimeField(_('Created'), blank=False, null=False, default=now)
    valid_until = DateTimeField(_('Valid Until'), blank=False, null=False, default=get_recovery_max_validity)
    key = CharField(_('Credential Recovery Key'), max_length=255, blank=False, null=False, default=get_recovery_key)

    def __str__(self):
        return '{} ({})'.format(str(self.uuid), self.user.username)
