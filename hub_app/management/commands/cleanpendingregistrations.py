"""
Clean up pending registrations from database

You should use a cron job to trigger this regularly.
"""
from django.core.management import BaseCommand
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from hub_app.models import HubUser


class Command(BaseCommand):
    """
    Management Command for cleaning up expired pending registrations
    """

    help = _('Delete pending registrations older than 3 days')

    def handle(self, *args, **options):
        expired_user_registrations = HubUser.objects.filter(
            pendingregistration__isnull=False,
            pendingregistration__valid_until__lt=now()
        )
        count = expired_user_registrations.count()
        self.stdout.write(_('Deleting %(count)s user accounts with expired registrations.') % {'count': count})
        if count > 0:
            expired_user_registrations.delete()
        self.stdout.write(self.style.SUCCESS(_('Done')))
