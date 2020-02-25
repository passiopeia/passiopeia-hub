"""
Clean up pending e-mail changes from database

You should use a cron job to trigger this regularly.
"""
from django.core.management import BaseCommand
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from hub_app.models import PendingEMailChange


class Command(BaseCommand):
    """
    Management Command for cleaning up expired e-mail changes
    """

    help = _('Delete e-mail changes recoveries older than 1 day')

    def handle(self, *args, **options):
        expired_changes = PendingEMailChange.objects.filter(valid_until__lt=now())
        count = expired_changes.count()
        self.stdout.write(_('Deleting %(count)s pending e-mail changes.') % {'count': count})
        if count > 0:
            expired_changes.delete()
        self.stdout.write(self.style.SUCCESS(_('Done')))
