"""
Pre Flight Check Command

This command checks the current installation for common configuration issues.
"""
from typing import Callable

from django.conf import settings
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Implementation, based on the Django BaseCommand
    """

    help = 'Checks for common configuration mistakes'

    def _perform_check(self, check_name: str, check_method: Callable[[], bool]) -> bool:
        """
        Common Check implementation

        :param str check_name: Name of the check for the logging
        :param Callable[[], bool] check_method: Method to be executed as the test, must result in a boolean

        :rtype: bool
        :returns: Test result as boolean, "True" on success, "False" otherwise
        """
        self.stdout.write('* Checking {}... '.format(check_name), ending='')
        result = check_method()
        if result:
            self.stdout.write(self.style.SUCCESS('passed'))
        else:
            self.stdout.write(self.style.ERROR('failed'))
        return result

    def check_django_secret(self) -> bool:
        """
        Check if the SECRET_KEY is not like it is shipped from the repository

        :rtype: bool
        :returns: True, if the SECRET_KEY is not like the one shipped from the repository
        """
        return self._perform_check(
            'SECRET_KEY',
            lambda: not settings.SECRET_KEY.upper().startswith('NEVER_USE_THIS_IN_PRODUCTION')
        )

    def check_debug(self) -> bool:
        """
        Check if the DEBUG mode is still on

        :rtype: bool
        :returns: True, if the DEBUG mode is off
        """
        return self._perform_check(
            'DEBUG',
            lambda: not settings.DEBUG
        )

    def check_allowed_hosts(self) -> bool:
        """
        Check if the ALLOWED_HOSTS config is not empty

        :rtype: bool
        :returns: True, if the ALLOWED_HOSTS list is not empty
        """
        return self._perform_check(
            'ALLOWED_HOSTS',
            lambda: isinstance(settings.ALLOWED_HOSTS, list) and len(settings.ALLOWED_HOSTS) > 0
        )

    def handle(self, *args, **options):
        passed = True
        self.stdout.write('Performing a Pre-Flight Check...')
        passed = self.check_django_secret() and passed
        passed = self.check_debug() and passed
        self.stdout.write('Pre-Flight Check finished.')
        if passed:
            self.stdout.write(self.style.SUCCESS('Pre-flight Check PASSED'))
        else:
            raise CommandError('Pre-flight Check FAILED')
