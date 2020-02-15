"""
Tests for the Registration Lib
"""
from django.test import SimpleTestCase, tag
from django.utils.timezone import now

from hub_app.reglib.key import get_registration_key
from hub_app.reglib.validity import get_registration_max_validity


class RegistrationKeyGenerationTest(SimpleTestCase):
    """
    Test the generation of registration key
    """

    def test_format(self):
        """
        Test the format of the key
        """
        key = get_registration_key()
        self.assertRegex(
            key,
            r'^[a-zA-Z0-9.\-_~]{250}$'
        )

    @tag('slow')
    def test_uniqueness(self):
        """
        Test Uniqueness of the keys
        """
        keys = []
        for _ in range(10000):
            key = get_registration_key()
            self.assertNotIn(key, keys)
            keys.append(key)


class RegistrationValidityTest(SimpleTestCase):
    """
    Test the validity Generation
    """

    def test_smoke(self):
        """
        No need to test the datetime package...
        """
        self.assertGreater(get_registration_max_validity(), now())
