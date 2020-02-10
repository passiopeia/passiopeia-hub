"""
Tests for the authentication backend
"""
from django.test import TestCase, RequestFactory

from hub_app.authlib.backend import TotpAuthenticationBackend
from hub_app.authlib.totp.token import get_possible_otps
from hub_app.models.users import HubUser


class AuthenticationDeniedTest(TestCase):
    """
    Tests for a denied authentication
    """

    @classmethod
    def setUpTestData(cls) -> None:
        user = HubUser.objects.create(
            username='mr_right',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        user.set_password('right_pass')  # nosec
        user.set_totp_secret(b'SUPERSECRETSUPER-SUPERSECRETSUPER')
        user.save()
        cls.request_factory = RequestFactory()

    def test_wrong_credentials(self):
        """
        Simple Test with wrong username, password and OTP in different combinations
        """
        test_items = (
            ('mr_right', 'wrong_pass'),
            ('mr_wrong', 'right_pass'),
        )
        for username, password in test_items:
            with self.subTest(msg='Testing with user "{}" and password "{}"'.format(username, password)):
                self.assertIsNone(
                    TotpAuthenticationBackend().authenticate(
                        self.request_factory.get('/'),
                        username=username,
                        password=password,
                        one_time_pw='123456'
                    )
                )

    def test_wrong_secret(self):
        """
        Test with correct username, password, but wrong OTP
        """
        test_items = ('000000', '999999', '111111', '222222')
        for otp in test_items:
            with self.subTest(msg='Testing with (wrong) otp "{}"'.format(otp)):
                self.assertIsNone(
                    TotpAuthenticationBackend().authenticate(  # nosec
                        self.request_factory.get('/'),
                        username='mr_right',
                        password='right_pass',
                        one_time_pw=otp
                    )
                )

    def test_invalid_secret(self):
        """
        Tests with correct username and password, but an (formal) invalid otp
        """
        test_items = ('00000', '11111', '99999', '0000000', '1111111', '9999999', '0000000000', '9999999999')
        for otp in test_items:
            with self.subTest(msg='Testing with formal invalid otp "{}"'.format(otp)):
                self.assertIsNone(
                    TotpAuthenticationBackend().authenticate(  # nosec
                        self.request_factory.get('/'),
                        username='mr_right',
                        password='right_pass',
                        one_time_pw=otp
                    )
                )

    def test_all_wrong(self):
        """
        Test with nothing correct
        """
        self.assertIsNone(
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw='000000'
            )
        )

    def test_only_one_part_wrong(self):
        """
        Testing with correct OTP, but one wrong other part
        """
        test_items = (
            ('mr_right', 'wrong_pass'),
            ('mr_wrong', 'right_pass'),
            ('', 'right_pass'),
            ('mr_right', ''),
            (None, 'right_pass'),
            ('mr_right', None),
        )
        for username, password in test_items:
            with self.subTest(msg='Testing with user "{}" and password "{}"'.format(username, password)):
                self.assertIsNone(
                    TotpAuthenticationBackend().authenticate(
                        self.request_factory.get('/'),
                        username=username,
                        password=password,
                        one_time_pw=get_possible_otps(b'SUPERSECRETSUPER-SUPERSECRETSUPER', 0, 0)[0]
                    )
                )


class AuthenticationSuccessTest(TestCase):
    """
    Test the good case - authentication succeeds
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_right',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        cls.user.set_password('right_pass')  # nosec
        cls.user.set_totp_secret(b'SUPERSECRETSUPER-SUPERSECRETSUPER')
        cls.user.save()
        cls.request_factory = RequestFactory()

    def test_all_good(self):
        """
        Everything is correct
        """
        self.assertEqual(
            self.user,
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw=get_possible_otps(b'SUPERSECRETSUPER-SUPERSECRETSUPER', 0, 0)[0]
            )
        )


class AuthenticationBlankNoneTest(TestCase):
    """
    What happens if one part is "None"?
    """

    @classmethod
    def setUpTestData(cls) -> None:
        user = HubUser.objects.create(
            username='mr_right',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        user.set_password('right_pass')  # nosec
        user.set_totp_secret(b'SUPERSECRETSUPER-SUPERSECRETSUPER')
        user.save()
        cls.request_factory = RequestFactory()

    def test_blank_or_none_data(self):
        """
        Test with one part is "None"
        """
        test_items = (
            (None, 'right_pass', '123456'),
            ('mr_right', None, '123456'),
            ('mr_right', 'right_pass', None),
            ('', 'right_pass', '123456'),
            ('mr_right', '', '123456'),
            ('mr_right', 'right_pass', ''),
            (None, None, '123456'),
            (None, 'right_pass', None),
            ('mr_right', None, None),
            ('', '', '123456'),
            ('', 'right_pass', ''),
            ('mr_right', '', ''),
            (None, None, None),
            ('', '', ''),
        )
        for username, password, token in test_items:
            with self.subTest(msg='Testing with user "{}", password "{}" and token "{}'.format(
                    username, password, token
            )):
                self.assertIsNone(
                    TotpAuthenticationBackend().authenticate(
                        self.request_factory.get('/'),
                        username=username,
                        password=password,
                        one_time_pw=token
                    )
                )


class InvalidInputLengthTest(TestCase):
    """
    Test how the Backend behaves with invalid input lengths
    """

    @classmethod
    def setUpTestData(cls) -> None:
        user = HubUser.objects.create(
            username='mr_right',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        user.set_password('right_pass')  # nosec
        user.set_totp_secret(b'SUPERSECRETSUPER-SUPERSECRETSUPER')
        user.save()
        cls.request_factory = RequestFactory()

    def test_invalid_lengths(self):
        """
        Test with invalid lengths
        """
        test_items = (
            ('mr_right', 'right_pass', '1234567'),
            ('mr_right', 'right_pass', '12345'),
            ('tobehonesthisusernameismuchtoolongandhasverymuchmorethantheallowednumberofcharacterstheresnoneedtocheck'
             'ifitexistsindatabasesodontwasteyourtimewiththisone', 'right_pass', '123456'),
            ('mr_right',
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan'
             'somepasswordsareextremelylongandcangetuptoonethousandcharssoletsrepeatthesecharsuntilwearegreaterthan',
             '123456')
        )
        for username, password, otp in test_items:
            with self.subTest(msg='Trying user "{}", password "{}" and otp "{}"'.format(username, password, otp)):
                self.assertIsNone(
                    TotpAuthenticationBackend().authenticate(
                        self.request_factory.get('/'),
                        username=username,
                        password=password,
                        one_time_pw=otp
                    )
                )


class UsernameCleanerTest(TestCase):
    """
    Test the username cleaning method
    """

    def test_cleaner(self):
        """
        Simple test of the cleaning method
        """
        test_items = (
            (' username ', 'username'),
            (' username', 'username'),
            ('username ', 'username'),
            ('user name', 'user name'),
            (' user name', 'user name'),
            ('user name ', 'user name'),
            (' user name ', 'user name'),
            ('  username  ', 'username'),
            ('  username', 'username'),
            ('username  ', 'username'),
            ('UserName', 'username'),
            ('USERNAME', 'username'),
            ('User Name', 'user name'),
            ('user Name', 'user name'),
            ('userName', 'username'),
            ('-userName', '-username'),
            ('username.', 'username.'),
            ('User.Name', 'user.name'),
            ('User.Name@server.com', 'user.name@server.com'),
        )
        for user_input, expected_result in test_items:
            with self.subTest(msg='User input is "{}", expecting "{}"'.format(user_input, expected_result)):
                self.assertEqual(expected_result, TotpAuthenticationBackend.clean_username(user_input))


class BurnedOtpTest(TestCase):
    """
    Test the handling of burned OTPs
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_right',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        cls.user.set_password('right_pass')  # nosec
        cls.user.set_totp_secret(b'SUPERSECRETSUPER-SUPERSECRETSUPER')
        cls.user.save()
        cls.request_factory = RequestFactory()

    def test_double_use_of_otp(self):
        """
        What happens, when a otp is used twice?
        """
        otp = get_possible_otps(b'SUPERSECRETSUPER-SUPERSECRETSUPER', 0, 0)[0]
        self.assertEqual(
            self.user,
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw=otp
            )
        )
        self.assertEqual(
            None,
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw=otp
            )
        )


class DoubleLoginBurnedOtpTest(TestCase):
    """
    Some additional no-double-use scenario
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_right',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        cls.user.set_password('right_pass')  # nosec
        cls.user.set_totp_secret(b'SUPERSECRETSUPER-SUPERSECRETSUPER')
        cls.user.save()
        cls.request_factory = RequestFactory()

    def test_separate_use_of_otp(self):
        """
        Test that logging in with independent OTPs works
        """
        tokens = get_possible_otps(b'SUPERSECRETSUPER-SUPERSECRETSUPER', 0, 1)
        self.assertEqual(
            self.user,
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw=tokens[0]
            )
        )
        self.assertEqual(
            self.user,
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw=tokens[1]
            )
        )


class UserWithNoTotpSecretSetTest(TestCase):
    """
    Users with no OTP secret shall not login
    """

    @classmethod
    def setUpTestData(cls) -> None:
        user = HubUser.objects.create(
            username='mr_right',
            is_active=True,
            is_staff=True,
            is_superuser=True,
            totp_secret=None
        )
        user.set_password('right_pass')  # nosec
        user.save()
        cls.request_factory = RequestFactory()

    def test_with_no_totp_secret_set(self):
        """
        Make sure the login attempt fails
        """
        self.assertIsNone(
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw='123456'
            )
        )


class InactiveUserTest(TestCase):
    """
    Inactive users shall not login
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_right',
            is_active=False,
            is_staff=True,
            is_superuser=True
        )
        cls.user.set_password('right_pass')  # nosec
        cls.user.set_totp_secret(b'SUPERSECRETSUPER-SUPERSECRETSUPER')
        cls.user.save()
        cls.request_factory = RequestFactory()

    def test_inactive_user(self):
        """
        User is not allowed to login
        """
        self.assertIsNone(
            TotpAuthenticationBackend().authenticate(  # nosec
                self.request_factory.get('/'),
                username='mr_right',
                password='right_pass',
                one_time_pw=get_possible_otps(b'SUPERSECRETSUPER-SUPERSECRETSUPER', 0, 0)[0]
            )
        )
