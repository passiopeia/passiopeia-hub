"""
Test the Token/OTP/Secret generation system
"""
from random import SystemRandom
from django.test import SimpleTestCase, tag

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.totp.token import get_possible_otps, create_encrypted_random_totp_secret, \
    create_random_totp_secret


class TokenGeneratorSmokeTest(SimpleTestCase):
    """
    Test the token generator
    """

    def test_token_generator(self):
        """
        Test token generation
        """
        test_items = (
            (b'12345678123456781234567812345678', -3, 3),
            (b'12345678123456781234567812345678', -1, 1),
            (b'12345678123456781234567812345678', -0, 0),
            (b'1234567812345678123456781234567812345678123456781234567812345678', -3, 3),
            (b'1234567812345678123456781234567812345678123456781234567812345678', -1, 1),
            (b'1234567812345678123456781234567812345678123456781234567812345678', -0, 0),
            (b'123456781234567812345678123456781234567812345678123456781234567812345678123456781234567812345678',
             -3, 3),
            (b'123456781234567812345678123456781234567812345678123456781234567812345678123456781234567812345678',
             -1, 1),
            (b'123456781234567812345678123456781234567812345678123456781234567812345678123456781234567812345678',
             -0, 0),
            (bytes(SystemRandom().getrandbits(8) for _ in range(32)), -3, 3),
            (bytes(SystemRandom().getrandbits(8) for _ in range(32)), -1, 1),
            (bytes(SystemRandom().getrandbits(8) for _ in range(32)), -0, 0),
            (bytes(SystemRandom().getrandbits(8) for _ in range(64)), -3, 3),
            (bytes(SystemRandom().getrandbits(8) for _ in range(64)), -1, 1),
            (bytes(SystemRandom().getrandbits(8) for _ in range(64)), -0, 0),
            (bytes(SystemRandom().getrandbits(8) for _ in range(96)), -3, 3),
            (bytes(SystemRandom().getrandbits(8) for _ in range(96)), -1, 1),
            (bytes(SystemRandom().getrandbits(8) for _ in range(96)), -0, 0),
        )
        for secret, offset_lower, offset_upper in test_items:
            with self.subTest('Testing with a secret of "{}", a lower offset of {} and an upper offset of {}'.format(
                    secret, offset_lower, offset_upper
            )):
                tokens = get_possible_otps(secret, offset_lower, offset_upper)
                self.assertIsNotNone(tokens)
                expected_count = abs(offset_upper) + abs(offset_lower) + 1
                self.assertEqual(
                    expected_count,
                    len(tokens)
                )
                for token in tokens:
                    self.assertRegex(token, r'^\d{6}$')


class SecretGeneratorSmokeTest(SimpleTestCase):
    """
    Smoke Tests for the Secret Generator
    """

    generator_lengths = (
        2 ** 0, 2 ** 1, 2 ** 2, 2 ** 3, 2 ** 4, 2 ** 5, 2 ** 6, 2 ** 7, 2 ** 8, 2 ** 9, 2 ** 10, 2 ** 11, 2 ** 12,
        2 ** 13, 2 ** 14, 2 ** 15, 2 ** 16,
        72, 96, 192,
    )

    random_sets = (
        (16, 10000),
        (32, 10000),
        (64, 1000),
        (72, 100),
        (96, 100),
    )

    def test_encrypted_secret_generator_default_length(self):
        """
        Test if a encrypted random secret has the required length
        """
        self.assertEqual(
            72,
            len(SymmetricCrypt().decrypt(create_encrypted_random_totp_secret()))
        )

    def test_encrypted_secret_generator_lengths(self):
        """
        Test different lengths
        """
        for test_item in self.generator_lengths:
            with self.subTest(msg='Testing with a length of {}'.format(test_item)):
                self.assertEqual(
                    test_item,
                    len(SymmetricCrypt().decrypt(create_encrypted_random_totp_secret(test_item)))
                )

    def test_secret_generator_default_length(self):
        """
        Test if an unencrypted secret has the required length
        """
        self.assertEqual(
            72,
            len(create_random_totp_secret())
        )

    def test_secret_generator_lengths(self):
        """
        Test if unencrypted secrets match the length
        """
        for test_item in self.generator_lengths:
            with self.subTest(msg='Testing with a length of {}'.format(test_item)):
                self.assertEqual(
                    test_item,
                    len(create_random_totp_secret(test_item))
                )

    @tag('slow')
    def test_encrypted_secret_generator_randomness(self):
        """
        Test the randomness of the encrypted secret generator
        """
        for length, amount in self.random_sets:
            with self.subTest(msg='Testing with a length of {} in {} iterations'.format(length, amount)):
                secrets = []
                for _ in range(amount):
                    secret = SymmetricCrypt().decrypt(create_encrypted_random_totp_secret(length))
                    self.assertNotIn(
                        secret,
                        secrets
                    )
                    secrets.append(secret)

    @tag('slow')
    def test_secret_generator_randomness(self):
        """
        Test the randomness of unencrypted secret generator
        """
        for length, amount in self.random_sets:
            with self.subTest(msg='Testing with a length of {} in {} iterations'.format(length, amount)):
                secrets = []
                for _ in range(amount):
                    secret = create_random_totp_secret(length)
                    self.assertNotIn(
                        secret,
                        secrets
                    )
                    secrets.append(secret)
