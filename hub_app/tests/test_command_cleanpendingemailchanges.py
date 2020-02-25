"""
Tests for the "cleanpendingemailchanges" command
"""
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now

from hub_app.management.commands import cleanpendingemailchanges
from hub_app.models import HubUser, PendingEMailChange


class DeleteOnFullDatabaseTest(TestCase):
    """
    Test on a full database
    """

    @classmethod
    def setUpTestData(cls):
        for i in range(100):
            user_pending_current = HubUser.objects.create_user(username='pending_current_{}'.format(i))
            PendingEMailChange.objects.create(user=user_pending_current, new_email='test@test.org')
            user_pending_old = HubUser.objects.create_user(username='expired_pending_current_{}'.format(i))
            expired_pending = PendingEMailChange.objects.create(user=user_pending_old, new_email='test@test.org')
            expired_pending.valid_until = now() - timedelta(seconds=1)
            expired_pending.save()
            HubUser.objects.create_user(username='real_user_{}'.format(i))

    def test_deletion_on_populated_database(self):
        """
        Test on populated database
        """
        self.assertEqual(200, PendingEMailChange.objects.count())
        self.assertEqual(100, PendingEMailChange.objects.filter(
            user__username__startswith='expired_pending_'
        ).count())
        self.assertEqual(300, HubUser.objects.all().count())
        with StringIO() as out:
            call_command(cleanpendingemailchanges.Command(), stdout=out)
            self.assertRegex(out.getvalue().strip(), r'(Done).{0,10}$')
        self.assertEqual(100, PendingEMailChange.objects.count())
        self.assertEqual(0, PendingEMailChange.objects.filter(
            user__username__startswith='expired_pending_'
        ).all().count())
        self.assertEqual(300, HubUser.objects.all().count())


class DeleteOnEmptyDatabaseTest(TestCase):
    """
    Run on an empty database
    """

    def test_delete_on_empty(self):
        """
        We are expecting no exception
        """
        with StringIO() as out:
            call_command(cleanpendingemailchanges.Command(), stdout=out)
            self.assertRegex(out.getvalue().strip(), r'(Done).{0,10}$')
