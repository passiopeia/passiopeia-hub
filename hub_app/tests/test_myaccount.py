"""
Simple Test for the MyAccount Start page
"""
from urllib.parse import quote

from django.test import TestCase
from django.urls import reverse

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser


class MyAccountTest(TestCase):
    """
    Test if one can access the view under different circumstances
    """

    url = reverse('ha:acc:overview')

    @classmethod
    def setUpTestData(cls):
        cls.secret = b'MyVerySecretTestSecretOnlyForTestingThingsInATest'
        cls.password = 'Y3t_an0th3R-C0O1:PASsW0RD!'
        cls.normal_user = HubUser.objects.create_user(username='normalo_user', first_name='Frank', email='t@test.org')
        cls.admin_user = HubUser.objects.create_superuser(username='supero_user')
        for test_user in [cls.normal_user, cls.admin_user]:  # type: HubUser
            test_user.set_password(cls.password)
            test_user.set_totp_secret(cls.secret)
            test_user.save()

    def _open(self):
        """
        Open the page
        """
        return self.client.get(self.url, follow=False)

    def test_anonymous_user(self):
        """
        Test access with an anonymous user
        """
        response = self._open()
        self.assertEqual(302, response.status_code)
        self.assertEqual('/hub/auth/login?next={}'.format(quote(self.url)), response.url)

    def test_normal_user(self):
        """
        Test access with a normal user
        """
        self.client.login(username=self.normal_user.username, password=self.password, one_time_pw=get_otp(self.secret))
        response = self._open()
        self.assertEqual(200, response.status_code)

    def test_admin_user(self):
        """
        Test access with a normal user
        """
        self.client.login(username=self.admin_user.username, password=self.password, one_time_pw=get_otp(self.secret))
        response = self._open()
        self.assertEqual(200, response.status_code)
