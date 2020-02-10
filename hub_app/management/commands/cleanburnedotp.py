"""
Clean up burned OTPs from database

You should use a cron job to trigger this regularly.
"""
import datetime

from django.core.management import BaseCommand
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from hub_app.models import BurnedOtp


class Command(BaseCommand):
    """
    Management Command for cleaning up old burned OTPs
    """

    help = _('Delete burned OTPs older than 2 hours')

    def handle_clean_burned_otp(self):
        """
        Remove burned OTPs that are older than 2 hours
        """
        the_oldest_one_to_keep = now() - datetime.timedelta(hours=2)
        old_entries = BurnedOtp.objects.filter(burned_timestamp__lt=the_oldest_one_to_keep)
        count = old_entries.count()
        self.stdout.write(_('Deleting %(count)s burned OTPs.') % {'count': count})
        if count > 0:
            old_entries.delete()
        self.stdout.write(self.style.SUCCESS(_('Done')))

    def handle(self, *args, **options):
        self.handle_clean_burned_otp()
