"""
Models required for registration
"""
from uuid import uuid4

from django.db.models import Model, UUIDField, CASCADE, DateTimeField, CharField, OneToOneField
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from hub_app.models.users import HubUser
from hub_app.reglib.key import get_registration_key
from hub_app.reglib.validity import get_registration_max_validity


class PendingRegistration(Model):
    """
    Store pending Registrations
    """

    class Meta:
        verbose_name = _('Pending Registration')
        verbose_name_plural = _('Pending Registrations')
        default_permissions = ('add', 'change', 'delete')
        permissions = ()

    uuid = UUIDField(_('UUID'), primary_key=True, blank=False, null=False, default=uuid4)
    user = OneToOneField(HubUser, unique=True, verbose_name=_('User'), blank=False, null=False, on_delete=CASCADE)
    created = DateTimeField(_('Created'), blank=False, null=False, default=now)
    valid_until = DateTimeField(_('Valid Until'), blank=False, null=False, default=get_registration_max_validity)
    key = CharField(_('Registration Key'), max_length=255, blank=False, null=False, default=get_registration_key)

    def __str__(self):
        return '{} ({})'.format(str(self.uuid), self.user.username)
