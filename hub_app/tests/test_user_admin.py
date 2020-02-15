"""
Test a roundtrip though the user admin
"""
from base64 import b32decode

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag, TestCase
from django.urls import reverse
from selenium.webdriver.firefox.webdriver import WebDriver

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser
from hub_app.tests.helper import firefox_webdriver_factory


@tag('slow', 'gui')
class UserAdminRoundtripTest(StaticLiveServerTestCase):
    """
    Selenium based roundtrip test
    """

    admin_username = 'admin_user_for_roundtrip'
    admin_password = 'S0meL355Serious!Password-Only4Test?'  # nosec
    admin_secret = b'IdonthaveacreativeSecretforthistestbutthisisenough'

    test_user = 'to_be_tested'
    test_password = 't03!B5$T35s13d1_ho!'  # nosec
    test_secret = b''

    def setUp(self) -> None:
        test_admin = HubUser.objects.create_superuser(
            username=self.admin_username,
            password=self.admin_password,
        )  # type: HubUser
        test_admin.set_totp_secret(self.admin_secret)
        test_admin.save()

    def _login_to_admin(self, webdriver: WebDriver):
        """
        Login to admin
        """
        webdriver.get('{}/admin/'.format(self.live_server_url))
        form = webdriver.find_element_by_css_selector('form[data-ui-relevance="main-login"]')
        form.find_element_by_css_selector('input[name="username"]').send_keys(self.admin_username)
        form.find_element_by_css_selector('input[name="password"]').send_keys(self.admin_password)
        form.find_element_by_css_selector('input[name="otp"]').send_keys(str(get_otp(self.admin_secret)))
        form.find_element_by_css_selector('button[type="submit"]').click()

    def _navigate_to_user_overview(self, webdriver: WebDriver):
        """
        Go to the User Model Overview Page
        """
        self.assertEqual('{}/admin/'.format(self.live_server_url), webdriver.current_url)
        webdriver.find_element_by_css_selector('table caption a[href="/admin/hub_app/"]').click()
        webdriver.find_element_by_css_selector('table tr td a[href="/admin/hub_app/hubuser/"]').click()

    def _open_new_user_form(self, webdriver: WebDriver):
        """
        Click to the new user form
        """
        self.assertEqual('{}/admin/hub_app/hubuser/'.format(self.live_server_url), webdriver.current_url)
        webdriver.find_element_by_css_selector('ul.object-tools li a.addlink').click()

    def _fill_new_user_form(self, webdriver: WebDriver):
        """
        Fill the new user form
        """
        self.assertEqual('{}/admin/hub_app/hubuser/add/'.format(self.live_server_url), webdriver.current_url)
        webdriver.find_element_by_id('id_username').send_keys(self.test_user)
        webdriver.find_element_by_id('id_password1').send_keys(self.test_password)
        webdriver.find_element_by_id('id_password2').send_keys(self.test_password)
        webdriver.find_element_by_css_selector('input[type="submit"][name="_continue"]').click()

    def _check_user_in_db(self):
        """
        Check if user is in DB
        """
        user = HubUser.objects.get(username=self.test_user)  # type: HubUser
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)
        self.test_secret = user.get_totp_secret()

    @staticmethod
    def _open_otp_assistant(webdriver: WebDriver):
        """
        Open the OTP Assistant
        """
        webdriver.find_element_by_css_selector(
            'div#id_get_totp_secret_length a[data-assistant-id="otp-assistant"]'
        ).click()
        webdriver.switch_to.window('otpAssistant')

    def _check_current_secret(self, webdriver: WebDriver, equal: bool):
        """
        Check the Secret that is stored in DB
        """
        assistant_field = webdriver.find_element_by_css_selector('div[data-user-field="secret"]')
        code = assistant_field.find_element_by_tag_name('code')
        if equal:
            self.assertEqual(self.test_secret, b32decode(code.text))
        else:
            self.assertNotEqual(self.test_secret, b32decode(code.text))

    @staticmethod
    def _hit_renew_button(webdriver: WebDriver):
        webdriver.find_element_by_css_selector('a[data-ui-relevance="renew-action"]').click()

    @staticmethod
    def _dont_renew_otp_secret(webdriver: WebDriver):
        """
        Hit the renew-button and the confirm-dialog
        """
        webdriver.switch_to.alert.dismiss()
        webdriver.switch_to.window('otpAssistant')

    @staticmethod
    def _renew_otp_secret(webdriver: WebDriver):
        """
        Hit the renew-button and the confirm-dialog
        """
        webdriver.switch_to.alert.accept()
        webdriver.switch_to.window('otpAssistant')

    def test(self):
        """
        Test Story
        """
        with firefox_webdriver_factory() as webdriver:
            self._login_to_admin(webdriver)
            self._navigate_to_user_overview(webdriver)
            self._open_new_user_form(webdriver)
            self._fill_new_user_form(webdriver)
            self._check_user_in_db()
            UserAdminRoundtripTest._open_otp_assistant(webdriver)
            self._check_current_secret(webdriver, True)
            UserAdminRoundtripTest._hit_renew_button(webdriver)
            UserAdminRoundtripTest._dont_renew_otp_secret(webdriver)
            self._check_current_secret(webdriver, True)
            UserAdminRoundtripTest._hit_renew_button(webdriver)
            UserAdminRoundtripTest._renew_otp_secret(webdriver)
            self._check_current_secret(webdriver, False)


class OtpAdminTest(TestCase):
    """
    Test Corner cases with direct request
    """

    test_superuser_username = 'test_otp_stuff_superuser'
    test_superuser_password = 'OhH0lyS*T!_A_P4ssw0RD!'  # nosec
    test_superuser_secret = b'ImTiredOfThinkingOfTestSecrets_SoItakeThis1!'

    @classmethod
    def setUpTestData(cls):
        test_user = HubUser.objects.create_superuser(
            username=cls.test_superuser_username,
            password=cls.test_superuser_password,
        )  # type: HubUser
        test_user.set_totp_secret(cls.test_superuser_secret)
        test_user.save()
        dumb_user_otp_assistant = HubUser.objects.create_user(  # nosec
            username='dumb_user_otp_assistant',
            password='12P4ssW0RD!->'
        )  # type: HubUser
        dumb_user_otp_assistant.totp_secret = None
        dumb_user_otp_assistant.save()
        dumb_user_regenerate = HubUser.objects.create_user(  # nosec
            username='dumb_user_regenerate',
            password='12P4ssW0RD!<-'
        )  # type: HubUser
        dumb_user_regenerate.save()

    def setUp(self) -> None:
        self.client.logout()
        self._login()

    def _login(self):
        """
        Log the client in
        """
        self.assertTrue(self.client.login(
            username=self.test_superuser_username,
            password=self.test_superuser_password,
            one_time_pw=get_otp(self.test_superuser_secret),
        ))

    def test_otp_assistant_non_existing_user_id(self):
        """
        Simply open a user that not exists
        """
        response = self.client.get(reverse('ha:admin:views.otp-assistant', kwargs={
            'user_id': '99887766'
        }))
        self.assertEqual(404, response.status_code)

    def test_otp_assistant_without_a_secret(self):
        """
        Test with a user that has no secret
        """
        response = self.client.get(reverse('ha:admin:views.otp-assistant', kwargs={
            'user_id': '2'
        }))
        self.assertEqual(200, response.status_code)
        self.assertInHTML('<code>-</code>', response.content.decode('utf-8'))

    def test_regenerate_non_existing_user_id(self):
        """
        Test the Regeneration with non exisiting user
        """
        response = self.client.get(reverse('ha:admin:actions.regenerate-otp-secret', kwargs={
            'user_id': '99887766'
        }))
        self.assertEqual(404, response.status_code)

    def test_regenerate_existing_user_id_without_next(self):
        """
        Test the Regeneration with exisiting user,
        and without next
        """
        response = self.client.get(reverse('ha:admin:actions.regenerate-otp-secret', kwargs={
            'user_id': '3'
        }))
        self.assertEqual(200, response.status_code)

    def test_qr_code_generation(self):
        """
        Test the Regeneration with non exisiting user
        """
        test_items = (
            # user_id, format, expected
            (2, 'png', 404),
            (2, 'svg', 404),
            (3, 'png', 200),
            (3, 'png', 200),
            (998877, 'svg', 404),
            (998877, 'png', 404),
        )
        for user_id, file_type, expected in test_items:
            with self.subTest(msg='Testing user ID "{}" with format "{}", expecting status "{}"'.format(
                    user_id, file_type, expected
            )):
                response = self.client.get(reverse('ha:admin:views.qr', kwargs={
                    'user_id': str(user_id),
                    'file_type': file_type
                }))
                self.assertEqual(expected, response.status_code)
