"""
Clean up pending credential recoveries from database

You should use a cron job to trigger this regularly.
"""
from django.core.management import BaseCommand
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from hub_app.models import PendingCredentialRecovery


class Command(BaseCommand):
    """
    Management Command for cleaning up expired pending credential recoveries
    """

    help = _('Delete pending credential recoveries older than 1 hour')

    def handle(self, *args, **options):
        expired_recoveries = PendingCredentialRecovery.objects.filter(valid_until__lt=now())
        count = expired_recoveries.count()
        self.stdout.write(_('Deleting %(count)s pending credential recoveries.') % {'count': count})
        if count > 0:
            expired_recoveries.delete()
        self.stdout.write(self.style.SUCCESS(_('Done')))
