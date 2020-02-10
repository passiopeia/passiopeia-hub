"""
Tests around the HubUser Model
"""
from random import SystemRandom

from cryptography.fernet import InvalidToken
from django.test import TestCase

from hub_app.models import HubUser


class SetTotpSecretConstraints(TestCase):
    """
    Test the secret validation
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test',
        )

    def test_totp_secret_too_short(self):
        """
        Test secrets that are too short
        """
        test_items = ('', 'a', 'aa', 'aaaaaaaa', 'aaaaaaaaaaaaaaaa', 'aaaaaaaaaaaaaaaaaaaaaaaa',
                      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        for test_item in test_items:
            with self.subTest(msg='Testing with "{}"'.format(test_item)):
                self.assertRaisesMessage(
                    ValueError,
                    'Secret must be at least 32 bytes long',
                    self.user.set_totp_secret,
                    test_item
                )

    def test_totp_secret_too_long(self):
        """
        Test secrets that are too long
        """
        test_items = (
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        )
        for test_item in test_items:
            with self.subTest(msg='Testing with "{}"'.format(test_item)):
                self.assertRaisesMessage(
                    ValueError,
                    'Secret must not be larger than 96 bytes',
                    self.user.set_totp_secret,
                    test_item
                )


class SetAndGetTotpSecretTest(TestCase):
    """
    Test getting and setting secrets from and to the database
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test',
        )

    def test_getter_setter(self):
        """
        Test getter and setter, executed after each other
        """
        test_items = (
            b'SOME-SECRET-DATA-SOMETHING-LIKE-LONG',
            b'SOME-SECRET-DATA-EXTRA-LONG-LONG-LONG-LONG',
            b'12345678123456781234567812345678',
            b'1234567812345678123456781234567812345678123456781234567812345678',
            b'123456781234567812345678123456781234567812345678123456781234567812345678123456781234567812345678',
            bytes(SystemRandom().getrandbits(8) for _ in range(32)),
            bytes(SystemRandom().getrandbits(8) for _ in range(64)),
            bytes(SystemRandom().getrandbits(8) for _ in range(96)),
        )
        for test_item in test_items:
            with self.subTest(msg='Testing with "{}"'.format(test_item)):
                self.user.set_totp_secret(test_item)
                self.user.save()
                extracted_item = self.user.get_totp_secret()
                self.assertEqual(test_item, extracted_item)


class GetNoneTotpSecretTest(TestCase):
    """
    Get a "None" TOTP secret from databasr
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test',
            totp_secret=None,
        )

    def test_none_getter(self):
        """
        Test with "None" in DB
        """
        self.assertIsNone(self.user.get_totp_secret())


class GetEmptyTotpSecretTest(TestCase):
    """
    Get an empty TOTP secret from databasr
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test',
            totp_secret=b'',
        )

    def test_emtpy_getter(self):
        """
        Test with empty '' in DB
        """
        self.assertRaises(
            InvalidToken,
            self.user.get_totp_secret
        )


class HubUserModelToStringMethodTest(TestCase):
    """
    Test the simple str method
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = HubUser.objects.create(
            username='mr_test',
        )

    def test_str_method(self):
        """
        Simple str smoke test
        """
        self.assertEqual(
            'mr_test',
            str(self.user)
        )
