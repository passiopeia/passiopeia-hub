"""
Test the Credential Recovery Process
"""
from django.test import TestCase
from django.urls import reverse

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser


class RegistrationSmokeTest(TestCase):
    """
    A simple Smoke test for the moment
    """

    test_username = 'test_registration_user'
    test_password = 'RegistrationPa55w0rd!'  # nosec
    test_secret = b'ANeatBitOfASecret-That-is-it-NotForProduction'

    @classmethod
    def setUpTestData(cls):
        cls.user = HubUser.objects.create_user(
            username=cls.test_username,
            password=cls.test_password
        )  # type: HubUser
        cls.user.set_totp_secret(cls.test_secret)
        cls.user.save()

    def setUp(self) -> None:
        self.client.logout()

    def _check_result(self, status_code=200):
        """
        Check how it worked
        """
        response = self.client.get(reverse('ha:reg:step.1'), follow=True)
        self.assertEqual(status_code, response.status_code)

    def test_not_logged_in(self):
        """
        Just call and check result
        """
        self._check_result()

    def test_logged_in(self):
        """
        Test with a Login
        """
        self.client.login(
            username=self.test_username,
            password=self.test_password,
            one_time_pw=get_otp(self.test_secret)
        )
        self._check_result(403)
