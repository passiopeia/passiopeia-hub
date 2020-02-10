"""
Models belonging to a User
"""
from typing import Optional
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db.models import BinaryField, Model, UUIDField, ForeignKey, CASCADE, CharField, DateTimeField
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.totp.token import create_encrypted_random_totp_secret


class HubUser(AbstractUser):
    """
    The HubUser is basically the standard Django user, but has an additional encrypted shared TOTP secret
    """

    totp_secret = BinaryField(
        _('TOTP Secret'),
        max_length=1024, null=True, blank=False,
        default=create_encrypted_random_totp_secret,
        help_text=_('Encrypted TOTP Secret')
    )

    def set_totp_secret(self, secret: bytes):
        """
        Set the TOTP Secret

        The TOTP Secret will be encrypted before it is saved to the database.

        :param bytes secret: The TOTP secret to be encrypted and saved to the database
        """
        if len(secret) < 32:
            raise ValueError(_('Secret must be at least 32 bytes long'))
        if len(secret) > 96:
            raise ValueError(_('Secret must not be larger than 96 bytes'))
        self.totp_secret = SymmetricCrypt().encrypt(secret)

    def get_totp_secret(self) -> Optional[bytes]:
        """
        Get the TOTP Secret

        This method gives you the unencrypted (decrypted) TOTP secret

        :rtype: Optional[bytes]
        :returns: The unencrypted secret or None if no secret is set
        """
        if self.totp_secret is None:
            return None
        return SymmetricCrypt().decrypt(self.totp_secret)

    def __str__(self):
        return '{}'.format(self.username)


class BurnedOtp(Model):
    """
    The BurnedOtp Model contains burned one-time passwords to make sure that every password is only used once
    """

    class Meta:
        verbose_name = _('Burned One Time Password')
        verbose_name_plural = _('Burned One Time Passwords')
        default_permissions = ()
        permissions = ()
        unique_together = (
            ('user', 'token'),
        )

    uuid = UUIDField(_('UUID'), primary_key=True, blank=False, null=False, default=uuid4)
    user = ForeignKey(HubUser, verbose_name=_('User'), blank=False, null=False, on_delete=CASCADE)
    token = CharField(_('OTP Token'), max_length=6, blank=False, null=False)
    burned_timestamp = DateTimeField(_('Burned Date/Time'), blank=False, null=False, default=now)

    def __str__(self):
        return '{} ({})'.format(self.token, self.user.username)
