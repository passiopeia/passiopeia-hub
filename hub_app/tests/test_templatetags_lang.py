"""
Tests for the Template Tag Lib 'hub_app_lang'
"""
from django.conf import settings
from django.test import SimpleTestCase, override_settings

from hub_app.templatetags.hub_app_lang import do_current_language


class CurrentLanguageTagTest(SimpleTestCase):
    """
    Test the 'current_language' tag
    """

    def test_with_default_language(self):
        """
        With default language
        """
        self.assertEqual(settings.LANGUAGE_CODE, do_current_language())

    @override_settings(LANGUAGE_CODE='de')
    def test_with_overridden_setting(self):
        """
        With overridden language
        """
        self.assertEqual('de', do_current_language())
