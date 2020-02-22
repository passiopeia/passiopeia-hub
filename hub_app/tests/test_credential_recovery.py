"""
Test the Credential Recovery Process
"""
import re
from base64 import b64decode
from json import loads
from urllib.parse import unquote

from bs4 import BeautifulSoup
from django.core import mail
from django.core.signing import Signer
from django.http import HttpResponse
from django.test import TestCase
from urllib3.util import parse_url

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.forgot_credentials import get_recovery_key
from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser, PendingRegistration, PendingCredentialRecovery


class CredentialRecoverySmokeTest(TestCase):
    """
    A simple Smoke test for the moment
    """

    username = 'test_cred_rec_user'
    password = 'S0m3EasyPa55w0rd!!'  # nosec
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
        response = self.client.get('/hub/auth/forgot-credentials/step-1', follow=True)
        self.assertEqual(200, response.status_code)

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


class BasicRecoveryTest(TestCase):
    """
    Test the basic recovery workflow for different user types
    """

    @classmethod
    def setUpTestData(cls):
        cls.secret = b'S0meT3stS3cr3t!-ButVery.Long!Must_match-the:Basic/RULES;'
        cls.password = 'pA55$W0RD'
        cls.active_user = HubUser.objects.create_user(username='active_user', is_active=True,
                                                      email='active@test.org', first_name='Active')
        cls.inactive_user = HubUser.objects.create_user(username='inactive_user', is_active=False,
                                                        email='inactive@test.org', first_name='Inactive')
        cls.user_with_pending_registration = HubUser.objects.create_user(username='user_in_reg', is_active=True,
                                                                         email='reg@test.org', first_name='Register')
        cls.pending_registration = PendingRegistration.objects.create(user=cls.user_with_pending_registration)
        for user in [cls.active_user, cls.inactive_user, cls.user_with_pending_registration]:  # type: HubUser
            user.set_totp_secret(cls.secret)
            user.set_password(cls.password)
            user.save()
        cls.user_1 = HubUser.objects.create_user(username='user_1', email='u@test.org', password=cls.password)
        cls.user_2 = HubUser.objects.create_user(username='user_2', email='u@test.org', password=cls.password)
        for user in [cls.user_1, cls.user_2]:  # type: HubUser
            user.set_totp_secret(cls.secret)
            user.save()

    def _start_recovery_process(self):
        """
        Open the recovery page
        """
        open_response = self.client.get('/hub/auth/forgot-credentials/step-1', follow=True)
        self.assertEqual(200, open_response.status_code)

    def __select_recovery_type(self, recovery_type: str):
        """
        Select the matching recovery type
        """
        select_response = self.client.post('/hub/auth/forgot-credentials/step-1', follow=True, data={
            'step1': recovery_type
        })
        self.assertEqual(200, select_response.status_code)
        self.assertEqual(
            '/hub/auth/forgot-credentials/step-2/{}'.format(recovery_type),
            select_response.request.get('PATH_INFO')
        )

    def _start_session(self, recovery_type: str):
        """
        Start a test session
        """
        self._start_recovery_process()
        self.__select_recovery_type(recovery_type)

    def _send_partial_credentials(self, endpoint: str, partial_credentials: dict):
        """
        Send partial credentials
        """
        partial_info_response = self.client.post('/hub/auth/forgot-credentials/step-2/{}'.format(endpoint),
                                                 data=partial_credentials)
        self.assertEqual(200, partial_info_response.status_code)
        return partial_info_response

    def __check_screen_message(self, response: HttpResponse):
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find('div', attrs={
            'class': 'card-body bg-light text-dark'
        }).find_next('h2')
        self.assertEqual('Thank you.', soup.text.strip())

    def __check_screen_message_duplicate(self, response: HttpResponse):
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find('div', attrs={
            'class': 'card-body bg-light text-dark'
        }).find_next('h2')
        self.assertEqual('Oh no...', soup.text.strip())

    def _check_success(self, response: HttpResponse, first_name: str, email: str):
        """
        Check the Response for success, also check mail existence
        """
        self.__check_screen_message(response)
        self.assertEqual(1, PendingCredentialRecovery.objects.count())
        self.assertEqual(1, len(mail.outbox))
        recovery_mail = mail.outbox[0]
        self.assertTrue('Hi {}!'.format(first_name) in str(recovery_mail.body))
        self.assertEqual(email, ''.join(recovery_mail.to))
        extract_link_regex = re.compile(r'.*(?P<url>http(s)?://.*step-3.*?)\s.*', re.MULTILINE | re.UNICODE | re.DOTALL)
        match = extract_link_regex.match(str(recovery_mail.body))
        self.assertIsNotNone(match)
        return match.group('url')

    def _check_no_success(self, response: HttpResponse):
        """
        No Recovery created
        """
        self.__check_screen_message(response)
        self.assertEqual(0, PendingCredentialRecovery.objects.count())
        self.assertEqual(0, len(mail.outbox))

    def _check_no_success_duplicate(self, response: HttpResponse):
        """
        No Recovery created
        """
        self.__check_screen_message_duplicate(response)
        self.assertEqual(0, PendingCredentialRecovery.objects.count())
        self.assertEqual(0, len(mail.outbox))

    def __extract_link(self, link: str):
        """
        Extract information from link
        """
        parsed_url = parse_url(link)
        self.assertIsNotNone(parsed_url)
        return {
            'query': parsed_url.query,
            'path': parsed_url.path,
            'auth': unquote(parsed_url.query[5:]),
            'uuid': parsed_url.path[-36:]
        }

    def __open_action(self, extracted_link: dict):
        """
        Open Action from Link
        """
        action_response = self.client.get(extracted_link['path'], data={
            'auth': extracted_link['auth']
        }, follow=True)
        self.assertEqual(200, action_response.status_code)

    def _check_username_reveal(self, link: str, user: str):
        """
        Check if the username is revealed
        """
        extracted_link = self.__extract_link(link)
        self.__open_action(extracted_link)
        # The bad ones
        test_items = (
            'doctored', ''
        )
        for auth in test_items:
            self.client.post(
                '/hub/auth/forgot-credentials/step-3/{}/reveal-username'.format(extracted_link['uuid']),
                data={
                    'auth': auth
                }
            )
        # And the good one
        username_response = self.client.post(
            '/hub/auth/forgot-credentials/step-3/{}/reveal-username'.format(extracted_link['uuid']),
            data={
                'auth': extracted_link['auth']
            }
        )
        self.assertEqual(200, username_response.status_code)
        self.assertIn('<strong><code>{}</code></strong>'.format(user), username_response.content.decode('utf-8'))
        self.assertEqual(0, PendingCredentialRecovery.objects.count())

    def _check_set_new_password(self, link: str):
        """
        Check setting the new password
        """
        new_password = 'T0tally_N3W!-Pa$$w0RD'  # nosec
        extracted_link = self.__extract_link(link)
        user_id = PendingCredentialRecovery.objects.get(uuid=extracted_link['uuid']).user.id
        self.__open_action(extracted_link)
        # First: Bad Tries
        test_items = (
            # auth, pw1, pw2
            (extracted_link['auth'], new_password, ''),
            (extracted_link['auth'], '', ''),
            (extracted_link['auth'], 'test', 'test'),
            (extracted_link['auth'], 'test1234', 'test1234'),
            (extracted_link['auth'], '1234567890', '12345567890'),
            ('', new_password, new_password),
            ('I_faked_the_auth!', new_password, new_password),
            ('', '', ''),
        )
        for auth, pw1, pw2 in test_items:
            self.client.post(
                '/hub/auth/forgot-credentials/step-3/{}/set-new-password'.format(extracted_link['uuid']),
                data={
                    'auth': auth,
                    'password': pw1,
                    'password_repeat': pw2
                },
                follow=True
            )
        # At last: Good Try
        password_response = self.client.post(
            '/hub/auth/forgot-credentials/step-3/{}/set-new-password'.format(extracted_link['uuid']),
            data={
                'auth': extracted_link['auth'],
                'password': new_password,
                'password_repeat': new_password
            },
            follow=True
        )
        self.assertEqual(200, password_response.status_code)
        self.assertEqual(0, PendingCredentialRecovery.objects.count())
        self.assertTrue(HubUser.objects.get(id=user_id).check_password(new_password))

    def _check_new_otp(self, link: str):
        """
        Check the new OTP setup
        """
        extracted_link = self.__extract_link(link)
        user_id = PendingCredentialRecovery.objects.get(uuid=extracted_link['uuid']).user.id
        self.__open_action(extracted_link)
        # The bad ones
        test_items = (
            'doctored-auth', ''
        )
        for auth in test_items:
            self.client.post(
                '/hub/auth/forgot-credentials/step-3/{}/reveal-new-otp-secret'.format(extracted_link['uuid']),
                data={
                    'auth': auth,
                },
                follow=True
            )
        otp_ready_response = self.client.post(
            '/hub/auth/forgot-credentials/step-3/{}/reveal-new-otp-secret'.format(extracted_link['uuid']),
            data={
                'auth': extracted_link['auth'],
            },
            follow=True
        )
        self.assertEqual(200, otp_ready_response.status_code)
        internal_session_data = str(b64decode(self.client.session.model.objects.first().session_data).decode('utf-8'))
        internal_session_data = internal_session_data[internal_session_data.index(':')+1:]
        internal_session_data = loads(internal_session_data)
        encrypted_otp_secret = b64decode(internal_session_data['encrypted_temporary_otp_secret'])
        new_otp_secret = SymmetricCrypt().decrypt(encrypted_otp_secret)
        # And the bad OTPs fist
        test_items = (
            # auth, otp
            (extracted_link['auth'], ''),
            (extracted_link['auth'], '999999'),
        )
        for auth, otp in test_items:
            self.client.post(
                '/hub/auth/forgot-credentials/step-3/{}/reveal-new-otp-secret/confirm'.format(extracted_link['uuid']),
                data={
                    'auth': auth,
                    'otp': otp
                },
                follow=True
            )
        otp_confirm_response = self.client.post(
            '/hub/auth/forgot-credentials/step-3/{}/reveal-new-otp-secret/confirm'.format(extracted_link['uuid']),
            data={
                'auth': extracted_link['auth'],
                'otp': get_otp(new_otp_secret)
            },
            follow=True
        )
        self.assertEqual(200, otp_confirm_response.status_code)
        self.assertEqual(0, PendingCredentialRecovery.objects.count())
        self.assertEqual(new_otp_secret, HubUser.objects.get(id=user_id).get_totp_secret())

    def test_active_user_password_recovery_happy_path(self):
        """
        Test with an active user a password recovery
        """
        self._start_session('password')
        response = self._send_partial_credentials('password', {
            'email': 'active@test.org',
            'username': 'active_user',
            'otp': get_otp(self.secret)
        })
        link = self._check_success(response, 'Active', 'active@test.org')
        self._check_set_new_password(link)

    def test_active_user_username_recovery_happy_path(self):
        """
        Test with an active user a password recovery
        """
        self._start_session('username')
        response = self._send_partial_credentials('username', {
            'email': 'active@test.org',
            'password': self.password,
            'otp': get_otp(self.secret)
        })
        link = self._check_success(response, 'Active', 'active@test.org')
        self._check_username_reveal(link, 'active_user')

    def test_active_user_otp_secret_recovery_happy_path(self):
        """
        Test with an active user a password recovery
        """
        self._start_session('otp-secret')
        response = self._send_partial_credentials('otp-secret', {
            'email': 'active@test.org',
            'username': 'active_user',
            'password': self.password,
        })
        link = self._check_success(response, 'Active', 'active@test.org')
        self._check_new_otp(link)

    def test_inactive_user_username(self):
        """
        Inactive user is not allowed to create a recovery, but we don't tell
        """
        self._start_session('username')
        response = self._send_partial_credentials('username', {
            'email': 'inactive@test.org',
            'otp': get_otp(self.secret),
            'password': self.password,
        })
        self._check_no_success(response)

    def test_inactive_user_password(self):
        """
        Inactive user is not allowed to create a recovery, but we don't tell
        """
        self._start_session('password')
        response = self._send_partial_credentials('password', {
            'email': 'inactive@test.org',
            'otp': get_otp(self.secret),
            'username': 'inactive_user',
        })
        self._check_no_success(response)

    def test_inactive_user_otp_secret(self):
        """
        Inactive user is not allowed to create a recovery, but we don't tell
        """
        self._start_session('otp-secret')
        response = self._send_partial_credentials('otp-secret', {
            'email': 'inactive@test.org',
            'username': 'inactive_user',
            'password': self.password,
        })
        self._check_no_success(response)

    def test_pending_registration_user_username(self):
        """
        User with a pending registration is not allowed to create a recovery, but we don't tell
        """
        self._start_session('username')
        response = self._send_partial_credentials('username', {
            'email': 'reg@test.org',
            'otp': get_otp(self.secret),
            'password': self.password,
        })
        self._check_no_success(response)

    def test_pending_registration_user_password(self):
        """
        User with a pending registration is not allowed to create a recovery, but we don't tell
        """
        self._start_session('password')
        response = self._send_partial_credentials('password', {
            'email': 'reg@test.org',
            'otp': get_otp(self.secret),
            'username': 'user_in_reg',
        })
        self._check_no_success(response)

    def test_pending_registration_user_otp_secret(self):
        """
        User with a pending registration is not allowed to create a recovery, but we don't tell
        """
        self._start_session('otp-secret')
        response = self._send_partial_credentials('otp-secret', {
            'email': 'reg@test.org',
            'username': 'user_in_reg',
            'password': self.password,
        })
        self._check_no_success(response)

    def test_duplicate_email_user_username(self):
        """
        User with a non-unique e-mail address is not allowed to create a recovery, and we tell
        """
        self._start_session('username')
        response = self._send_partial_credentials('username', {
            'email': 'u@test.org',
            'otp': get_otp(self.secret),
            'password': self.password,
        })
        self._check_no_success_duplicate(response)

    def test_duplicate_email_user_password(self):
        """
        User with a non-unique e-mail address is not allowed to create a recovery, and we tell
        """
        self._start_session('password')
        response = self._send_partial_credentials('password', {
            'email': 'u@test.org',
            'otp': get_otp(self.secret),
            'username': 'user_1',
        })
        self._check_no_success_duplicate(response)

    def test_duplicate_email_user_otp_secret(self):
        """
        User with a non-unique e-mail address is not allowed to create a recovery, and we tell
        """
        self._start_session('otp-secret')
        response = self._send_partial_credentials('otp-secret', {
            'email': 'u@test.org',
            'username': 'user_1',
            'password': self.password,
        })
        self._check_no_success_duplicate(response)

    def test_wrong_credentials_username(self):
        """
        User with wrong credentials is not allowed to create a recovery, but we don't tell
        """
        test_items = (
            # email, otp, password
            ('active@test.org', get_otp(self.secret, 1), 'AbsolutelyWr0ng!'),
            ('active@test.org', get_otp(self.secret, -10), self.password),
            ('active.wrong@test.org', get_otp(self.secret, 1), self.password),
        )
        for email, otp, password in test_items:
            with self.subTest(msg='Testing E-Mail="{}", OTP="{}", Password="{}"'.format(email, otp, password)):
                self._start_session('username')
                response = self._send_partial_credentials('username', {
                    'email': email,
                    'otp': otp,
                    'password': password,
                })
                self._check_no_success(response)

    def test_wrong_credentials_password(self):
        """
        User with wrong credentials is not allowed to create a recovery, but we don't tell
        """
        test_items = (
            # email, otp, username
            ('active@test.org', get_otp(self.secret, 1), 'bad_username'),
            ('active@test.org', get_otp(self.secret, -10), 'active_user'),
            ('active.wrong@test.org', get_otp(self.secret, 1), 'active_user'),
        )
        for email, otp, username in test_items:
            with self.subTest(msg='Testing E-Mail="{}", OTP="{}", Username="{}"'.format(email, otp, username)):
                self._start_session('password')
                response = self._send_partial_credentials('password', {
                    'email': email,
                    'otp': otp,
                    'username': username,
                })
                self._check_no_success(response)

    def test_wrong_credentials_otp_secret(self):
        """
        User with wrong credentials is not allowed to create a recovery, but we don't tell
        """
        test_items = (
            # email, username, password
            ('active@test.org', 'bad_username', self.password),
            ('active@test.org', 'active_user', 'AbsolutelyWr0ng!'),
            ('active.wrong@test.org', 'active_user', self.password),
        )
        for email, username, password in test_items:
            with self.subTest(msg='Testing E-Mail="{}", Username="{}", Password="{}"'.format(
                    email, username, password
            )):
                self._start_session('otp-secret')
                response = self._send_partial_credentials('otp-secret', {
                    'email': email,
                    'username': username,
                    'password': password,
                })
                self._check_no_success(response)

    def test_step1_invalid_form(self):
        """
        Test that the Step 1 form can handle Bad Input
        """
        test_items = (
            'first_name', 'email', 'e-mail', 'None', ''
        )
        for test_item in test_items:
            with self.subTest(msg='Testing with recovery type="{}"'.format(test_item)):
                self._start_recovery_process()
                select_response = self.client.post('/hub/auth/forgot-credentials/step-1', follow=True, data={
                    'step1': test_item
                })
                self.assertEqual(200, select_response.status_code)
                self.assertEqual(
                    '/hub/auth/forgot-credentials/step-1',
                    select_response.request.get('PATH_INFO')
                )

    def test_step2_password_invalid_form(self):
        """
        Test that the step2-password form can handle bad input
        """
        test_items = (
            # email, username, otp
            ('?', 'seems_valid', '123456'),
            ('valid@email.com', '?', '123456'),
            ('valid@email.com', 'seems_valid', '??????'),
            ('', 'seems_valid', '123456'),
            ('valid@email.com', '', '123456'),
            ('valid@email.com', 'seems_valid', ''),
            ('?', '?', '??????'),
            ('', '', ''),
        )
        for email, username, otp in test_items:
            with self.subTest(msg='Testing with E-Mail="{}", Username="{}", OTP="{}"'.format(email, username, otp)):
                self._start_session('password')
                response = self._send_partial_credentials('password', partial_credentials={
                    'email': email,
                    'username': username,
                    'otp': otp
                })
                self.assertEqual(200, response.status_code)
                self.assertEqual(
                    '/hub/auth/forgot-credentials/step-2/password',
                    response.request.get('PATH_INFO')
                )

    def test_step2_username_invalid_form(self):
        """
        Test that the step2-username form can handle bad input
        """
        test_items = (
            # email, password, otp
            ('?', 'Val1d_PA$sW0RD!', '123456'),
            ('valid@email.com', '?', '123456'),
            ('valid@email.com', 'Val1d_PA$sW0RD!', '??????'),
            ('', 'seems_valid', '123456'),
            ('valid@email.com', '', '123456'),
            ('valid@email.com', 'Val1d_PA$sW0RD!', ''),
            ('?', '?', '??????'),
            ('', '', ''),
        )
        for email, password, otp in test_items:
            with self.subTest(msg='Testing with E-Mail="{}", Password="{}", OTP="{}"'.format(email, password, otp)):
                self._start_session('username')
                response = self._send_partial_credentials('username', partial_credentials={
                    'email': email,
                    'password': password,
                    'otp': otp
                })
                self.assertEqual(200, response.status_code)
                self.assertEqual(
                    '/hub/auth/forgot-credentials/step-2/username',
                    response.request.get('PATH_INFO')
                )

    def test_step2_otp_secret_invalid_form(self):
        """
        Test that the step2-otp-secret form can handle bad input
        """
        test_items = (
            # email, username, password
            ('?', 'seems_valid', 'Val1d_PA$sW0RD!'),
            ('valid@email.com', '?', 'Val1d_PA$sW0RD!'),
            ('valid@email.com', 'seems_valid', '?'),
            ('', 'seems_valid', 'Val1d_PA$sW0RD!'),
            ('valid@email.com', '', 'Val1d_PA$sW0RD!'),
            ('valid@email.com', 'seems_valid', ''),
            ('?', '?', '?'),
            ('', '', ''),
        )
        for email, username, password in test_items:
            with self.subTest(msg='Testing with E-Mail="{}", Username="{}", Password="{}"'.format(
                    email, username, password
            )):
                self._start_session('otp-secret')
                response = self._send_partial_credentials('otp-secret', partial_credentials={
                    'email': email,
                    'username': username,
                    'password': password
                })
                self.assertEqual(200, response.status_code)
                self.assertEqual(
                    '/hub/auth/forgot-credentials/step-2/otp-secret',
                    response.request.get('PATH_INFO')
                )


class InvalidLinksFromEmailTest(TestCase):
    """
    Sometimes, there are invalid links from the E-Mails. Let's test them.
    """

    def test_link_behaviour(self):
        """
        Bad Links from E-Mails
        """
        test_links = (
            # link, data, status code
            ('/hub/auth/forgot-credentials/step-3/0fbf05ad-025e-4913-8435-265350b985a2', {}, 200),
            ('/hub/auth/forgot-credentials/step-3/0fbf05ad-025e-4913-8435-265350b985a2', {'auth': ''}, 200),
            ('/hub/auth/forgot-credentials/step-3/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', {}, 404),
            ('/hub/auth/forgot-credentials/step-3/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', {'auth': ''}, 404),
            ('/hub/auth/forgot-credentials/step-3/11111111-1111-1111-1111-111111111111', {}, 200),
            ('/hub/auth/forgot-credentials/step-3/11111111-1111-1111-1111-111111111111', {'auth': ''}, 200),
            ('/hub/auth/forgot-credentials/step-3/0fbf05ad-025e-4913-8435-265350b985a2', {
                'auth': Signer(salt='0fbf05ad-025e-4913-8435-265350b985a2').sign('MuchTooShort')
            }, 200),
            ('/hub/auth/forgot-credentials/step-3/0fbf05ad-025e-4913-8435-265350b985a2', {
                'auth': Signer(salt='0fbf05ad-025e-4913-8435-265350b985ax').sign(get_recovery_key())
            }, 200),
            ('/hub/auth/forgot-credentials/step-3/0fbf05ad-025e-4913-8435-265350b985a2', {
                'auth': Signer(salt='0fbf05ad-025e-4913-8435-265350b985a2').sign(get_recovery_key())
            }, 200),
        )
        for link, data, expected_status in test_links:
            with self.subTest(msg='Testing "{}"'.format(link)):
                response = self.client.get(link, data=data)
                self.assertEqual(expected_status, response.status_code)
                if expected_status == 200:
                    self.assertIn('Sorry, this link seems to be invalid', response.content.decode('utf-8'))
