"""
Tests for the URL configuration of the Home Page.
"""
from django.conf import settings
from django.test import TestCase

from hub_app.views.home import HomeView


class HomeViewUrlsRedirectTest(TestCase):
    """
    Test the redirects to the matching URL
    """

    def test_redirect_from_base_url(self):
        """
        If the base URL is called, an 302 should be raised
        """
        response = self.client.get('/', follow=False)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/{:s}/hub/'.format(settings.LANGUAGE_CODE), response.url)

    def test_404_from_direct_call(self):
        """
        Test if the URL to home is build up correctly in case of a non-i18n request
        """
        response = self.client.get('/hub/', follow=False)
        self.assertEqual(404, response.status_code)

    def test_redirect_from_i18n_call(self):
        """
        Test if the URL to home is build up correctly in case of a non-i18n request
        """
        response = self.client.get('/en/', follow=False)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/{:s}/hub/'.format(settings.LANGUAGE_CODE), response.url)


class HomeViewSmokeTest(TestCase):
    """
    Test if the Home Page loads without primary issues
    """

    def test_with_django_internal_client(self):
        """
        This is literally only a smoke test. If the page comes up with a status 200, everything is considered fine in
        this case. There should be a lot of more precise tests for the page's contents and functions.

        At least it checks that the HomeView was triggered
        """
        response = self.client.get('/', follow=True)
        self.assertEqual(200, response.status_code)
        context_data = getattr(response, 'context_data', None)
        self.assertIsInstance(context_data, dict)
        self.assertIsInstance(context_data.get('view', None), HomeView)
