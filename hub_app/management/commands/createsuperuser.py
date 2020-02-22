"""
Override the Django 'createsuperuser' command

hub_app superusers need a TOTP secret
"""
import argparse
import binascii
from base64 import b32decode
from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from hub_app.models import HubUser


def get_input():  # pragma: no cover
    """
    Get Input Abstraction
    """
    return input()  # nosec


def get_masked_input(prompt: str):  # pragma: no cover
    """
    Get Password Abstraction
    """
    return getpass(prompt=prompt)


class Command(BaseCommand):
    """
    Create a 'hub_app' superuser
    """

    requires_migrations_checks = True
    requires_system_checks = True

    help = _('Create a superuser for the hub_app')

    def add_arguments(self, parser: argparse.ArgumentParser):
        """
        Add the four fields to fill as parameters
        """
        parser.add_argument(
            '-u', '--username',
            nargs='?', required=False, type=str,
            help=_('Username for the new superuser; must be unique')
        )
        parser.add_argument(
            '-p', '--password',
            nargs='?', required=False, type=str,
            help=_('Password for the new superuser')
        )
        parser.add_argument(
            '-s', '--secret',
            nargs='?', required=False, type=str,
            help=_('BASE32 encoded shared secret for TOTP')
        )

    def get_from_user_input(self, field, masked: bool = False) -> str:
        """
        Get User Input for a field

        :param field: Field Name
        :param masked: Shall the input be masked?
        :rtype: str
        :returns: The User Input

        :raises CommandError: When something is wrong with the input
        """
        if masked:
            data = get_masked_input(prompt='{}: '.format(field))
        else:
            self.stdout.write('{}: '.format(field), ending='')
            data = get_input()
        if data is None:
            raise CommandError(_('"%(field)s" is required') % {'field': field})
        data = data.strip()
        if len(data) == 0:
            raise CommandError(_('"%(field)s" is required') % {'field': field})
        return data

    def database_operation(self, username: str, password: str, secret: bytes):
        """
        Create the superuser in the database

        :param str username: The Username
        :param str password: The Password
        :param bytes secret: The Secret (binary format)

        :raises CommandError: When something is wrong
        """
        try:
            HubUser.objects.get(username=username)
            raise CommandError(_('The user "%(username)s" already exists.') % {'username': username})
        except HubUser.DoesNotExist:
            with transaction.atomic():
                tx_id = transaction.savepoint()
                try:
                    superuser = HubUser.objects.create_superuser(
                        username=username,
                        password=password,
                    )  # type: HubUser
                    superuser.set_totp_secret(secret)
                    superuser.save()
                    self.stdout.write(self.style.SUCCESS(_('Superuser "%(username)s" created successfully') % {
                        'username': username
                    }))
                    transaction.savepoint_commit(tx_id)
                except ValueError as ex:
                    transaction.savepoint_rollback(tx_id)
                    raise CommandError(_('Unable to create user "%(username)s": %(message)s') % {
                        'username': username,
                        'message': str(ex)
                    })

    def validate_input_and_create_superuser(self, username: str, password: str, secret: str):
        """
        Check all fields, then create a superuser

        :param str username: The Username
        :param str password: The Password
        :param str secret: The Secret (BASE32 format)

        :raises CommandError: When something is wrong
        """
        try:
            ASCIIUsernameValidator()(username)
        except ValidationError as ex:
            raise CommandError(_('Username "%(username)s" is invalid: %(message)s') % {
                'username': username, 'message': ex.message
            })
        try:
            validate_password(password)
        except ValidationError as ex:
            raise CommandError('{}: {}'.format(
                _('The password is invalid'),
                ' '.join(ex.messages)
            ))
        try:
            secret_bin = b32decode(secret)
        except binascii.Error as ex:
            raise CommandError(_('Invalid TOTP Secret: %(message)s') % {
                'message': str(ex)
            })
        self.database_operation(username, password, secret_bin)

    def handle(self, *args, **options):
        username = options.get('username', None)
        password = options.get('password', None)
        secret = options.get('secret', None)

        if username is None:
            username = self.get_from_user_input(_('Username'))
        if password is None:
            password = self.get_from_user_input(_('Password'), True)
        if secret is None:
            secret = self.get_from_user_input(_('Secret (BASE32 format)'))
        self.validate_input_and_create_superuser(username.lower(), password, secret)
