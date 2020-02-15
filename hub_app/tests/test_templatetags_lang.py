"""
Tests for the Template Tag Lib 'hub_app_lang'
"""
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.template import RequestContext
from django.test import SimpleTestCase, override_settings, TestCase, RequestFactory, tag

from hub_app.templatetags.hub_app_lang import do_current_language, do_language_selector
from hub_app.tests.helper import firefox_webdriver_factory


def _evaluate_document_language(document_content: str, expected_value: str) -> bool:
    """
    Check the body for the correct set language
    """
    soup = BeautifulSoup(document_content, 'html.parser').find('html')
    page_lang = soup['lang']
    return page_lang == expected_value


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
        with self.subTest(msg='Basic Context Setup'):
            self.assertIsInstance(do_language_selector(test_rqc).get('next_url'), str)
            self.assertEqual('/', do_language_selector(test_rqc).get('next_url'))
            self.assertIsInstance(do_language_selector(test_rqc).get('instance'), str)
        found = []
        for i in range(100):
            with self.subTest(msg='Uniqueness of Instance ID in Run {}'.format(i + 1)):
                instance_uuid = do_language_selector(test_rqc).get('instance')
                self.assertNotIn(instance_uuid, found)
                found.append(instance_uuid)

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


@tag('slow', 'gui')
class LanguageSelectorTagUsageTest(StaticLiveServerTestCase):
    """
    Test using the language selector on the home page
    """

    changes = (
        # accept, first, select, expectation
        ('en', 'en', (
            ('en', 'en'),
            ('de', 'de'),
        )),
        ('de', 'de', (
            ('en', 'en'),
            ('de', 'de'),
        )),
        ('', 'en', (
            ('en', 'en'),
            ('de', 'de'),
        )),
        ('xx', 'en', (
            ('en', 'en'),
            ('de', 'de'),
        ))
    )

    def test_language_change_on_page(self):
        """
        Test a complete workflow through the form
        """
        for accept_header, first_lang, test_cases in self.changes:
            for test_case in test_cases:
                to_be_selected, expected = test_case
                with self.subTest(msg='Calling with "{}", expecting "{}" first, selecting "{}", expecting "{}"'.format(
                        accept_header, first_lang, to_be_selected, expected
                )):
                    with firefox_webdriver_factory(accept_language=accept_header) as webdriver:
                        webdriver.get('{}/'.format(self.live_server_url))
                        self.assertTrue(_evaluate_document_language(webdriver.page_source, first_lang))
                        language_selector_forms = webdriver.find_elements_by_xpath(
                            '//form[starts-with(@id, "language_selector_")]'
                        )
                        self.assertGreaterEqual(len(language_selector_forms), 1)
                        form = language_selector_forms[0]
                        # Open the Language Dropdown
                        drop_downs = form.find_elements_by_css_selector('button.dropdown-toggle')
                        self.assertEqual(1, len(drop_downs))
                        drop_downs[0].click()
                        # Check, if there are buttons for every language in the settings
                        buttons = form.find_elements_by_css_selector(
                            'div.dropdown-menu > button[type="submit"]'
                        )
                        self.assertEqual(len(settings.LANGUAGES), len(buttons))
                        # Check, if the correct element is selected
                        active_buttons = form.find_elements_by_css_selector(
                            'div.dropdown-menu > button[type="submit"].active'
                        )
                        self.assertEqual(1, len(active_buttons))
                        active_button = active_buttons[0]
                        self.assertEqual(first_lang, active_button.get_attribute('value'))
                        # Click the button for the next language
                        click_buttons = form.find_elements_by_css_selector(
                            'div.dropdown-menu > button[type="submit"][value="{}"]'.format(to_be_selected)
                        )
                        self.assertEqual(1, len(click_buttons))
                        click_buttons[0].click()
                        # Now, check if the page shows the expected lang
                        self.assertTrue(_evaluate_document_language(webdriver.page_source, expected))
