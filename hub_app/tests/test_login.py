"""
Testing Login (and Logout a bit)
"""
from bs4 import BeautifulSoup
from django.test import TestCase

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser


class LoginBaseTest(TestCase):
    """
    Basic test of the Login Functionality
    """

    username = 'test_user_login'
    password = 'test_password_1'  # nosec
    otp_secret = b's0methingSecr3tKes$ToUseInTestAndAlsoExtraLong!'

    @classmethod
    def setUpTestData(cls):
        cls.user = HubUser.objects.create_user(
            username=cls.username,
            password=cls.password,
            first_name='Test-Franz',
        )  # type: HubUser
        cls.user.set_totp_secret(cls.otp_secret)
        cls.user.save()

    def _check_message(self, url: str, expected: str):
        """
        Helper Method to check the message on the start page

        :param str url: URL to call
        :param str expected: What's to expect from the message
        """
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find('div', attrs={
            'data-ui-relevance': 'message',
            'class': 'alert alert-success alert-dismissible fade show',
            'role': 'alert'
        })
        self.assertEqual(expected, soup.text.strip())

    def test_login_success_and_logout(self):
        """
        Test for the good case
        """
        response = self.client.get('/hub/auth/login')
        self.assertEqual(200, response.status_code)
        response = self.client.post('/hub/auth/login', {
            'username': self.username, 'password': self.password, 'otp': get_otp(self.otp_secret)
        })
        self.assertEqual(302, response.status_code)
        self.assertEqual('/hub/', response.url)
        self._check_message(response.url, 'Hey Test-Franz, welcome to Passiopeia Hub!')
        response = self.client.get('/hub/auth/logout')
        self.assertEqual(302, response.status_code)
        self.assertEqual('/hub/', response.url)
        self._check_message(response.url, 'Logout successful.')

    def test_login_failed(self):
        """
        Tests for the bad cases
        """
        test_items = (
            # user, passw, otp, expected
            ('', '', '',
             'This field is required.'),  # Empty Strings
            ('user1', 'password1', 'WRONG1',
             'Username or password wrong, or one time password invalid.'),  # Everything wrong
            (self.username, 'password2', 'WRONG2',
             'Username or password wrong, or one time password invalid.'),  # Username OK
            ('user3', self.password, 'WRONG3',
             'Username or password wrong, or one time password invalid.'),  # Password OK
            ('user4', 'password4', get_otp(self.otp_secret),
             'Username or password wrong, or one time password invalid.'),  # OTP ok
            (self.username, self.password, 'WRONG5',
             'Username or password wrong, or one time password invalid.'),  # OTP invalid
            (self.username, self.password, get_otp(self.otp_secret, -2),
             'Username or password wrong, or one time password invalid.'),  # OTP too old
            (self.username, self.password, get_otp(self.otp_secret, +2),
             'Username or password wrong, or one time password invalid.'),  # OTP too young
            (self.username, self.password, get_otp(self.otp_secret + b'1'),
             'Username or password wrong, or one time password invalid.'),  # OTP not matching to secret
        )
        for username, password, otp, expected in test_items:
            with self.subTest(msg='Testing user="{}", password="{}", otp="{}"'.format(username, password, otp)):
                self.client.logout()
                response = self.client.get('/hub/auth/login')
                self.assertEqual(200, response.status_code)
                response = self.client.post('/hub/auth/login', {
                    'username': username, 'password': password, 'otp': otp
                })
                self.assertEqual(200, response.status_code)
                soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find('form', attrs={
                    'data-ui-relevance': 'main-login'
                }).find_next('div', attrs={
                    'role': 'alert',
                    'class': 'alert alert-danger'
                })
                self.assertEqual(expected, soup.text.strip())
