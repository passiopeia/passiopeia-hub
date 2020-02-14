"""
Check our apps.py
"""
from django.test import SimpleTestCase

from hub_app.apps import HubAppConfig


class AppsPyTest(SimpleTestCase):
    """
    Simple Check
    """

    def test_name(self):
        """
        Check the name
        """
        self.assertEqual('hub_app', HubAppConfig.name)
