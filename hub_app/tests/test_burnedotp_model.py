"""
Test the burned OTP model
"""
from django.test import TestCase

from hub_app.models import HubUser, BurnedOtp


class BurnedOtpModelToStringMethodTest(TestCase):
    """
    Test the simple str method
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test_otp',
        )
        cls.otp = BurnedOtp.objects.create(
            user=cls.user,
            token='123456'
        )

    def test_str_method(self):
        """
        Simple str smoke test
        """
        self.assertEqual(
            '123456 (mr_test_otp)',
            str(self.otp)
        )
