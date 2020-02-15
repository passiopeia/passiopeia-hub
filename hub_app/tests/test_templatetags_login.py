"""
Test for the Login Template Tags
"""
from bs4 import BeautifulSoup
from django.conf import settings
from django.template import RequestContext
from django.test import SimpleTestCase, RequestFactory, TestCase

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser
from hub_app.templatetags.hub_app_login import do_login_menu


class LoginMenuTemplateTagSimpleTest(SimpleTestCase):
    """
    Test if the method delivers a prepared dict
    """

    def test_required_data(self):
        """
        Test existence of required data
        """
        request_context = RequestContext(RequestFactory().get('/some/test/url'))
        template_context = do_login_menu(request_context)
        self.assertIsInstance(template_context, dict)
        with self.subTest(msg='Testing "next_url"'):
            self.assertEqual('/some/test/url', template_context.get('next_url'))
        for field in ['login_url', 'logout_url', 'account_url', 'register_url', 'instance', 'user']:
            with self.subTest(msg='Testing "{}"'.format(field)):
                self.assertIn(field, template_context)


class LoginMenuPopulationTest(TestCase):
    """
    Test how the menu is populated
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = HubUser.objects.create_user(  # nosec
            username='test_loginmenu',
            password='test_login_menu_1'
        )  # type: HubUser
        cls.user.set_totp_secret(b'MyVerySecretSecretSecretOnlyForThisTestSecretSecret')
        cls.user.save()

    def _get_links(self):
        """
        Get the links from the document
        """
        response = self.client.get('/', follow=True)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find('div', attrs={
            'data-ui-relevance': 'login-menu'
        })
        links = soup.find_all_next('a', attrs={
            'class': 'dropdown-item'
        })
        return links

    def _test_links(self, links, list_of_urls):
        """
        Test the links that appeared
        """
        self.assertEqual(len(links), len(list_of_urls))
        for index, value in enumerate(list_of_urls):
            with self.subTest(msg='Testing for Link {}'.format(index)):
                link = links[index]
                self.assertTrue(str(link['href']).startswith(str(value)))

    def test_not_logged_in(self):
        """
        Test with an anonymous user
        """
        links = self._get_links()
        self._test_links(links, [settings.REGISTER_URL, settings.LOGIN_URL])
        self.assertEqual('{}?next=/hub/'.format(str(settings.LOGIN_URL)), links[1]['href'])

    def test_logged_in(self):
        """
        Test with a logged in user
        """
        self.assertTrue(self.client.login(  # nosec
            username='test_loginmenu', password='test_login_menu_1',
            one_time_pw=get_otp(b'MyVerySecretSecretSecretOnlyForThisTestSecretSecret')
        ))
        links = self._get_links()
        self._test_links(links, [settings.MY_ACCOUNT_URL, settings.LOGOUT_URL])
