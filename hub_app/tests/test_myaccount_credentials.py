"""
MyAccount Credentials Test
"""
from base64 import b64decode
from json import loads

from django.urls import reverse

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser
from hub_app.tests.test_myaccount import MyAccountTest


class OverviewPageTest(MyAccountTest):
    """
    Check access to the overview page
    """

    url = reverse('ha:acc:credentials')


class PasswordPageTest(MyAccountTest):
    """
    Check the password page
    """

    url = reverse('ha:acc:credentials.password')

    def test_round_trip(self):
        """
        Test the complete round-trip with wrong inputs and finally a good one
        """
        self.client.login(username=self.normal_user.username, password=self.password, one_time_pw=get_otp(self.secret))
        self._open()
        wrong_tries = (
            # old, new1, new2
            ('', '', ''),
            (self.password, '', ''),
            (self.password, 'cool_new!Passw0RD!', ''),
            ('', 'cool_new!Passw0RD!', ''),
            ('', 'cool_new!Passw0RD!', 'cool_new!Passw0RD!'),
            ('wrong_password', 'cool_new!Passw0RD!', 'cool_new!Passw0RD!'),
            (self.password, 'cool_new!Passw0RD!-1', 'cool_new!Passw0RD!-2'),
            (self.password, '0123456789', '0123456789'),
            ('', '0123456789', '0123456789'),
            (self.password, 'testtest', 'testtest'),
            ('', 'testtest', 'testtest'),
            (self.password, self.normal_user.username + '_1!', self.normal_user.username + '_1!'),
        )
        for old, new1, new2 in wrong_tries:
            with self.subTest(msg='Testing with old="{}", new1="{}", new2="{}"'.format(old, new1, new2)):
                response = self.client.post(self.url, data={
                    'old_password': old,
                    'new_password1': new1,
                    'new_password2': new2,
                }, follow=False)
                self.assertEqual(200, response.status_code)
                self.assertTrue(HubUser.objects.get(username=self.normal_user.username).check_password(self.password))
        with self.subTest(msg='Testing with good data'):
            response = self.client.post(self.url, data={
                'old_password': self.password,
                'new_password1': 'cool_new!Passw0RD!',
                'new_password2': 'cool_new!Passw0RD!',
            }, follow=False)
            self.assertEqual(302, response.status_code)
            self.assertEqual('/hub/auth/login?next=/hub/my-account/credentials/password', response.url)
            self.assertTrue(HubUser.objects.get(username=self.normal_user.username).check_password(
                'cool_new!Passw0RD!'
            ))


class OtpSecretPageTest(MyAccountTest):
    """
    Check the otp secret page
    """

    url = reverse('ha:acc:credentials.otp-secret')

    def test_round_trip(self):
        """
        Test the complete Round Trip with wrong inputs and finally a good one
        """
        self.client.login(username=self.normal_user.username, password=self.password, one_time_pw=get_otp(self.secret))
        old_secret = self.normal_user.get_totp_secret()
        self._open()
        test_otps = (
            '', '1', '22', '333', '4444', '55555', '666666', 'aaaaaa', 'a1b2c3'
        )
        for test_otp in test_otps:
            with self.subTest(msg='Sending OTP "{}" without creating a secret before'.format(test_otp)):
                response = self.client.post(self.url, data={'otp_confirm': test_otp}, follow=False)
                self.assertEqual(200, response.status_code)
                self.assertEqual(old_secret, HubUser.objects.get(id=self.normal_user.id).get_totp_secret())
        for expect in (True, False):
            with self.subTest(msg='Creating a secret, expecting "{}"'.format(expect)):
                response = self.client.put(self.url)
                self.assertEqual(200, response.status_code)
                self.assertJSONEqual(response.content, {'secret_created': expect})
                self.assertEqual(old_secret, HubUser.objects.get(id=self.normal_user.id).get_totp_secret())
        session_data = str(b64decode(self.client.session.model.objects.first().session_data).decode('utf-8'))
        session_data = loads(session_data[session_data.index(':')+1:])
        new_otp_secret = SymmetricCrypt().decrypt(b64decode(session_data['encrypted_new_totp_secret']))
        test_otps = [
            '', '1', '22', '333', '4444', '55555', 'aaaaaa', 'a1b2c3'
        ] + [get_otp(new_otp_secret, -10)]
        for test_otp in test_otps:
            with self.subTest(msg='Sending OTP "{}" which is wrong'.format(test_otp)):
                response = self.client.post(self.url, data={'otp_confirm': test_otp}, follow=False)
                self.assertEqual(200, response.status_code)
                self.assertEqual(old_secret, HubUser.objects.get(id=self.normal_user.id).get_totp_secret())
        with self.subTest(msg='Testing with correct OTP'):
            response = self.client.post(self.url, data={'otp_confirm': get_otp(new_otp_secret)}, follow=False)
            self.assertEqual(200, response.status_code)
            self.assertNotEqual(old_secret, HubUser.objects.get(id=self.normal_user.id).get_totp_secret())
            self.assertEqual(new_otp_secret, HubUser.objects.get(id=self.normal_user.id).get_totp_secret())
