from django.conf import settings
from django.core.management import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Checks for common configuration mistakes'

    def _perform_check(self, check_name, check_method):
        self.stdout.write('* Checking {}... '.format(check_name), ending='')
        result = check_method()
        if result:
            self.stdout.write(self.style.SUCCESS('passed'))
        else:
            self.stdout.write(self.style.ERROR('failed'))
        return result

    def check_django_secret(self) -> bool:
        return self._perform_check(
            'SECRET_KEY',
            lambda: not settings.SECRET_KEY.upper().startswith('NEVER_USE_THIS_IN_PRODUCTION')
        )

    def check_debug(self) -> bool:
        return self._perform_check(
            'DEBUG',
            lambda: not settings.DEBUG
        )

    def check_allowed_hosts(self) -> bool:
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
