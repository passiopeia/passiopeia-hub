"""
Test the pending email change model
"""
from django.test import TestCase
from django.utils.timezone import now

from hub_app.models import HubUser
from hub_app.models.my_account import PendingEMailChange


class PendingEMailChangeModelTest(TestCase):
    """
    Test the simple str method
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test_pending_e-mail-change',
        )
        cls.pending_email_change = PendingEMailChange.objects.create(
            user=cls.user,
        )

    def test_str_method(self):
        """
        Simple str smoke test
        """
        self.assertEqual(
            '{} (mr_test_pending_e-mail-change)'.format(str(self.pending_email_change.uuid)),
            str(self.pending_email_change)
        )

    def test_auto_fields_created(self):
        """
        Test the auto fields: created
        """
        self.assertIsNotNone(self.pending_email_change.created)
        self.assertLessEqual(self.pending_email_change.created, now())

    def test_auto_fields_valid_until(self):
        """
        Test the auto fields: valid_until
        """
        self.assertIsNotNone(self.pending_email_change.valid_until)
        self.assertGreater(self.pending_email_change.valid_until, now())

    def test_auto_fields_key(self):
        """
        Test the auto fields: key
        """
        self.assertIsNotNone(self.pending_email_change.key)
        self.assertRegex(
            self.pending_email_change.key,
            r'^[a-zA-Z0-9$=^]{250}$'
        )

    def test_user(self):
        """
        Test the user mapping
        """
        self.assertEqual(self.user, self.pending_email_change.user)
