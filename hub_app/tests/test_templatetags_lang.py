"""
Tests for the Template Tag Lib 'hub_app_lang'
"""
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.template import RequestContext
from django.test import SimpleTestCase, override_settings, TestCase, RequestFactory

from hub_app.templatetags.hub_app_lang import do_current_language, do_language_selector
from hub_app.tests.helper import firefox_webdriver_factory


def _evaluate_document_language(document_content: str, expected_value: str) -> bool:
    """
    Check the body for the correct set language
    """
    soup = BeautifulSoup(document_content, 'html.parser').find('html')
    return soup['lang'] == expected_value


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


class LanguageSelectorTagTest(TestCase):
    """
    Test the 'language_selector' tag
    """

    language_codes_to_be_tested = (
        # value, expectation
        ('de', 'de'),
        ('en', 'en'),
        ('xy', 'en'),
        ('', 'en'),
        ('not_a_lang', 'en')
    )

    def test_context(self):
        """
        Test if the context is set
        """
        factory = RequestFactory()
        test_rqc = RequestContext(factory.get('/'))
        self.assertIsInstance(do_language_selector(test_rqc).get('rqc'), RequestContext)
        self.assertEqual(test_rqc, do_language_selector(test_rqc).get('rqc'))

    def test_language_selection_by_http_header(self):
        """
        Test with HTTP_ACCEPT_LANGUAGE header
        """
        for header_value, expected_value in self.language_codes_to_be_tested:
            with self.subTest(msg='Setting Header to "{}", expecting "{}"'.format(header_value, expected_value)):
                response = self.client.get('/', HTTP_ACCEPT_LANGUAGE=header_value, follow=True)
                self.assertTrue(_evaluate_document_language(response.content.decode('utf-8'), expected_value))

    def test_language_selection_by_cookie(self):
        """
        Test with the language cookie
        """
        for cookie_value, expected_value in self.language_codes_to_be_tested:
            with self.subTest(msg='Setting Cookie to "{}", expecting "{}"'.format(cookie_value, expected_value)):
                self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: cookie_value})
                response = self.client.get('/', follow=True)
                self.assertTrue(_evaluate_document_language(response.content.decode('utf-8'), expected_value))

    def test_colliding_language_selection_by_cookie_and_http_header(self):
        """
        Test what happens when the HTTP_LANGUAGE_ACCEPT header collides with the cookie
        """
        combinations = (
            # cookie, header, expectation
            ('de', 'en', 'de'),
            ('en', 'de', 'en'),
            ('de', 'de', 'de'),
            ('en', 'en', 'en'),
            ('xy', 'en', 'en'),
            ('xy', 'de', 'de'),
            ('en', 'xy', 'en'),
            ('de', 'xy', 'de'),
            ('xy', 'xy', 'en'),
            ('', 'en', 'en'),
            ('', 'de', 'de'),
            ('en', '', 'en'),
            ('de', '', 'de'),
            ('', '', 'en'),
        )
        for cookie_value, header_value, expected_value in combinations:
            with self.subTest(msg='Setting Cookie to "{}", header to "{}", expecting "{}"'.format(
                    cookie_value, header_value, expected_value
            )):
                self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: cookie_value})
                response = self.client.get('/', HTTP_ACCEPT_LANGUAGE=header_value, follow=True)
                self.assertTrue(_evaluate_document_language(response.content.decode('utf-8'), expected_value))


class LanguageSelectorTagUsageTest(StaticLiveServerTestCase):
    """
    Test using the language selector on the home page
    """

    def test_language_change_on_page(self):
        changes = (
            # accept, to, expectation
            ('en', (
                ('en', 'en'),
                ('de', 'de'),
            )),
            ('de', (
                ('en', 'en'),
                ('de', 'de'),
            )),
            ('', (
                ('en', 'en'),
                ('de', 'de'),
            ))
        )
        for accept_header, test_cases in changes:
            with self.subTest(msg='Accept-Language-Header for WebDriver is "{}"'.format(accept_header)):
                for test_case in test_cases:
                    to_be_selected, expected = test_case
                    with self.subTest(msg='Selecting "{}", expecting "{}"'.format(to_be_selected, expected)):
                        with firefox_webdriver_factory(accept_language=accept_header) as wd:
                            pass

