"""
Tests for the Account Lib
"""
from django.test import SimpleTestCase, tag
from django.utils.timezone import now

from hub_app.accountlib.email import get_email_key, get_email_max_validity


class EMailChangeKeyGenerationTest(SimpleTestCase):
    """
    Test the generation of e-mail change
    """

    def test_format(self):
        """
        Test the format of the key
        """
        key = get_email_key()
        self.assertRegex(
            key,
            r'^[a-zA-Z0-9$=^]{250}$'
        )

    @tag('slow')
    def test_uniqueness(self):
        """
        Test Uniqueness of the keys
        """
        keys = []
        for _ in range(10000):
            key = get_email_key()
            self.assertNotIn(key, keys)
            keys.append(key)


class EMailChangeValidityTest(SimpleTestCase):
    """
    Test the validity Generation
    """

    def test_smoke(self):
        """
        No need to test the datetime package...
        """
        self.assertGreater(get_email_max_validity(), now())
