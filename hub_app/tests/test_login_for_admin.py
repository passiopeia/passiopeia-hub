"""
Test Login Integration for Admin Area
"""
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser
from hub_app.tests.helper import firefox_webdriver_factory


class RedirectToHubLoginTest(StaticLiveServerTestCase):
    """
    Test that a request to the Admin Area is redirected to the Hub Login
    """

    def setUp(self) -> None:
        self.super_user = HubUser.objects.create_superuser(  # nosec
            username='superuser_admin_redirect_test',
            password='my_super_duper_complex_p455s0RD!',
            first_name='Admin'
        )  # type: HubUser
        self.super_user.set_totp_secret(b'SuperUsersTestSecretForASimpleLoginTestAgainstTheAdminArea!')
        self.super_user.save()

    def test_for_correct_login_page(self):
        """
        Simple Request Check
        """
        test_items = (
            # admin_url, intermediate_urls, expected_url
            ('/admin', ('/admin/', '/admin/login/?next=/admin/',),
             '/hub/auth/login?next=/admin/login/%3Fnext%3D/admin/'),
            ('/admin/', ('/admin/login/?next=/admin/',),
             '/hub/auth/login?next=/admin/login/%3Fnext%3D/admin/'),
            ('/admin/auth/group/', ('/admin/login/?next=/admin/auth/group/',),
             '/hub/auth/login?next=/admin/login/%3Fnext%3D/admin/auth/group/'),
        )
        for admin_url, intermediate_urls, expected_url in test_items:
            with self.subTest(msg='Testing URL "{}", expecting "{}"'.format(admin_url, expected_url)):
                response = self.client.get(admin_url, follow=False)
                for intermediate_url in intermediate_urls:
                    self.assertIn(response.status_code, (301, 302,))
                    self.assertEqual(intermediate_url, response.url)
                    response = self.client.get(response.url, follow=False)
                self.assertEqual(302, response.status_code)
                self.assertEqual(expected_url, response.url)

    @tag('slow', 'gui')
    def test_login_as_superuser_roundtrip(self):
        """
        Roundtrip with superuser
        """
        with firefox_webdriver_factory() as firefox:
            firefox.get('{}/admin/auth/group/'.format(self.live_server_url))
            self.assertEqual(
                '{}/hub/auth/login?next=/admin/login/%3Fnext%3D/admin/auth/group/'.format(
                    self.live_server_url
                 ),
                firefox.current_url
            )
            form = firefox.find_element_by_xpath('//form[@data-ui-relevance="main-login"]')
            # Check the next
            next_url = form.find_element_by_css_selector('input[type="hidden"][name="next"]')
            self.assertEqual('/admin/login/?next=/admin/auth/group/', next_url.get_attribute('value'))
            # fill out the form
            form.find_element_by_css_selector('input[name="username"]').send_keys('superuser_admin_redirect_test')
            form.find_element_by_css_selector('input[name="password"]').send_keys('my_super_duper_complex_p455s0RD!')
            otp = str(get_otp(b'SuperUsersTestSecretForASimpleLoginTestAgainstTheAdminArea!'))
            form.find_element_by_css_selector('input[name="otp"]').send_keys(otp)
            # do the login
            form.find_element_by_css_selector('button[type="submit"]').click()
            # Are we there?
            self.assertEqual(
                '{}/admin/'.format(
                    self.live_server_url
                 ),
                firefox.current_url
            )
