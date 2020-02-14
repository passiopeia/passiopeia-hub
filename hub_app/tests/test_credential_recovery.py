"""
Test the Credential Recovery Process
"""
from django.test import TestCase

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser


class CredentialRecoverySmokeTest(TestCase):
    """
    A simple Smoke test for the moment
    """

    username = 'test_cred_rec_user'
    password = 'S0m3EasyPa55w0rd!!'
    secret = b'NaOnlyASecret-Enough-4aTestRunButNotForProd'

    @classmethod
    def setUpTestData(cls):
        cls.user = HubUser.objects.create_user(
            username=cls.username,
            password=cls.password
        )  # type: HubUser
        cls.user.set_totp_secret(cls.secret)
        cls.user.save()

    def setUp(self) -> None:
        self.client.logout()

    def _check_result(self):
        """
        Check how it worked
        """
        r = self.client.get('/hub/auth/forgot-credentials', follow=True)
        self.assertEqual(200, r.status_code)

    def test_smoke_not_logged_in(self):
        """
        Just call and check result
        """
        self._check_result()

    def test_smoke_logged_in(self):
        """
        Test with a Login
        """
        self.client.login(
            username=self.username,
            password=self.password,
            one_time_pw=get_otp(self.secret)
        )
        self._check_result()
