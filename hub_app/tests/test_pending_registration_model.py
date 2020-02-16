"""
Test the pending registration model
"""
from django.test import TestCase
from django.utils.timezone import now

from hub_app.models import HubUser, PendingRegistration


class PendingRegistrationModelTest(TestCase):
    """
    Test the simple str method
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test_pending_registration',
        )
        cls.pending_reg = PendingRegistration.objects.create(
            user=cls.user
        )

    def test_str_method(self):
        """
        Simple str smoke test
        """
        self.assertEqual(
            '{} (mr_test_pending_registration)'.format(str(self.pending_reg.uuid)),
            str(self.pending_reg)
        )

    def test_auto_fields_created(self):
        """
        Test the auto fields: created
        """
        self.assertIsNotNone(self.pending_reg.created)
        self.assertLessEqual(self.pending_reg.created, now())

    def test_auto_fields_valid_until(self):
        """
        Test the auto fields: valid_until
        """
        self.assertIsNotNone(self.pending_reg.valid_until)
        self.assertGreater(self.pending_reg.valid_until, now())

    def test_auto_fields_key(self):
        """
        Test the auto fields: key
        """
        self.assertIsNotNone(self.pending_reg.key)
        self.assertRegex(
            self.pending_reg.key,
            r'^[a-zA-Z0-9.\-_~]{250}$'
        )

    def test_user(self):
        """
        Test the user mapping
        """
        self.assertEqual(self.user, self.pending_reg.user)
