"""
Test the pending registration model
"""
from django.test import TestCase
from django.utils.timezone import now

from hub_app.models import HubUser, PendingCredentialRecovery


class PendingCredentialRecoveryModelTest(TestCase):
    """
    Test the simple str method
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test_pending_credential_recovery',
        )
        cls.pending_recovery = PendingCredentialRecovery.objects.create(
            user=cls.user,
            recovery_type='password'
        )

    def test_str_method(self):
        """
        Simple str smoke test
        """
        self.assertEqual(
            '{} (mr_test_pending_credential_recovery)'.format(str(self.pending_recovery.uuid)),
            str(self.pending_recovery)
        )

    def test_field_type(self):
        """
        Test the Recovery Type
        """
        self.assertEqual('password', self.pending_recovery.recovery_type)

    def test_auto_fields_created(self):
        """
        Test the auto fields: created
        """
        self.assertIsNotNone(self.pending_recovery.created)
        self.assertLessEqual(self.pending_recovery.created, now())

    def test_auto_fields_valid_until(self):
        """
        Test the auto fields: valid_until
        """
        self.assertIsNotNone(self.pending_recovery.valid_until)
        self.assertGreater(self.pending_recovery.valid_until, now())

    def test_auto_fields_key(self):
        """
        Test the auto fields: key
        """
        self.assertIsNotNone(self.pending_recovery.key)
        self.assertRegex(
            self.pending_recovery.key,
            r'^[a-zA-Z0-9$/:;,]{250}$'
        )

    def test_user(self):
        """
        Test the user mapping
        """
        self.assertEqual(self.user, self.pending_recovery.user)
