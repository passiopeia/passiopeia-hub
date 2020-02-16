"""
Test the Credential Recovery Process
"""
import re
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core import mail
from django.core.mail import EmailMessage
from django.core.signing import Signer
from django.test import TestCase, tag
from django.urls import reverse
from selenium.webdriver.firefox.webdriver import WebDriver

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser, PendingRegistration
from hub_app.tests.helper import firefox_webdriver_factory


class RegistrationSmokeTest(TestCase):
    """
    A simple Smoke test for the moment
    """

    test_username = 'test_registration_user'
    test_password = 'RegistrationPa55w0rd!'  # nosec
    test_secret = b'ANeatBitOfASecret-That-is-it-NotForProduction'

    @classmethod
    def setUpTestData(cls):
        cls.user = HubUser.objects.create_user(
            username=cls.test_username,
            password=cls.test_password
        )  # type: HubUser
        cls.user.set_totp_secret(cls.test_secret)
        cls.user.save()

    def setUp(self) -> None:
        self.client.logout()

    def _check_result(self, status_code=200):
        """
        Check how it worked
        """
        response = self.client.get(reverse('ha:reg:step.1'), follow=True)
        self.assertEqual(status_code, response.status_code)

    def test_not_logged_in(self):
        """
        Just call and check result
        """
        self._check_result()

    def test_logged_in(self):
        """
        Test with a Login
        """
        self.client.login(
            username=self.test_username,
            password=self.test_password,
            one_time_pw=get_otp(self.test_secret)
        )
        self._check_result(403)


@tag('slow', 'gui')
class RegistrationRoundTripTest(StaticLiveServerTestCase):
    """
    Test the registration process with a full GUI test
    """

    @classmethod
    def setUpClass(cls):
        super(RegistrationRoundTripTest, cls).setUpClass()
        cls.webdriver = firefox_webdriver_factory()  # type: WebDriver

    @classmethod
    def tearDownClass(cls):
        cls.webdriver.quit()
        super(RegistrationRoundTripTest, cls).tearDownClass()

    def setUp(self) -> None:
        HubUser.objects.create_user(username='already_there')

    def _begin_registration(self):
        """
        Begin with the registration
        """
        self.webdriver.get('{}/'.format(self.live_server_url))
        menu = self.webdriver.find_element_by_xpath('//div[@data-ui-relevance="login-menu"]')
        menu.find_element_by_xpath('./button').click()
        menu.find_element_by_css_selector('div.dropdown-menu a.dropdown-item:first-child').click()
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-1'))

    def __fill_step1_form(self, user, first_name, last_name, email):
        """
        Fill the step 1 form
        """
        form = self.webdriver.find_element_by_css_selector('form[data-ui-relevance="main-reg-1"]')
        username_field = form.find_element_by_id('id_username')
        username_field.clear()
        username_field.send_keys(user)
        first_name_field = form.find_element_by_id('id_first_name')
        first_name_field.clear()
        first_name_field.send_keys(first_name)
        last_name_field = form.find_element_by_id('id_last_name')
        last_name_field.clear()
        last_name_field.send_keys(last_name)
        email_field = form.find_element_by_id('id_email')
        email_field.clear()
        email_field.send_keys(email)
        form.find_element_by_css_selector('button[type="submit"]').click()

    def _fill_form_step1_existing_user(self):
        """
        Fill the form for step 1 with existing user
        """
        self.__fill_step1_form('already_there', 'Tester', 'Testhausen', 'test@test.org')
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-1'))

    def _fill_form_step1_bad_email(self):
        """
        Fill the form for step 1 with bad email
        """
        self.__fill_step1_form('not_already_there', 'Tester', 'Testhausen', 'test-test.org')
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-1'))

    def _fill_form_step1_empty_first_name(self):
        """
        Fill the form for step 1 with empty first name
        """
        self.__fill_step1_form('not_already_there', '', 'Testhausen', 'test@test.org')
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-1'))

    def _fill_form_step1_all_wrong(self):
        """
        Fill the form for step 1 with much wrong
        """
        self.__fill_step1_form('already_there', '', 'Testhausen', 'test-test.org')
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-1'))

    def _fill_form_step1_with_valid_data(self):
        """
        Fill with valid data
        """
        self.__fill_step1_form('test_user', 'Tester', 'Testhausen', 'test@test.org')
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-1'))

    def _check_mail(self):
        """
        Check the mails that has been sent
        """
        self.assertEqual(1, len(mail.outbox))
        reg_mail = mail.outbox[0]  # type: EmailMessage
        self.assertEqual(['test@test.org'], reg_mail.to)
        self.assertEqual(settings.EMAIL_REGISTRATION_FROM, reg_mail.from_email)
        self.assertEqual(settings.EMAIL_REGISTRATION_SUBJECT, reg_mail.subject)
        self.assertTrue('Hi Tester!' in str(reg_mail.body))
        extract_link_regex = re.compile(r'.*(?P<url>http(s)?://.*step-2.*?)\s.*', re.MULTILINE | re.UNICODE | re.DOTALL)
        match = extract_link_regex.match(str(reg_mail.body))
        self.assertIsNotNone(match)
        link = match.group('url')
        self.assertIsNotNone(link)
        return link

    def _begin_step2(self, next_url: str):
        """
        Start with step two, with the link from the mail
        """
        self.webdriver.get(next_url)
        self.assertEqual(next_url, self.webdriver.current_url)

    @staticmethod
    def __get_valid_otp():
        """
        Get a valid TOTP
        """
        new_user = HubUser.objects.get(username='test_user')
        return get_otp(new_user.get_totp_secret())

    @staticmethod
    def __get_invalid_otp():
        """
        Get an invalid TOTP
        """
        new_user = HubUser.objects.get(username='test_user')
        return get_otp(new_user.get_totp_secret(), -10)

    def __fill_step2_form(self, pw1, pw2, otp):
        """
        Fill the step 2 form
        """
        form = self.webdriver.find_element_by_css_selector('form[data-ui-relevance="main-reg-2"]')
        pw1_field = form.find_element_by_id('id_password1')
        pw1_field.clear()
        pw1_field.send_keys(pw1)
        pw2_field = form.find_element_by_id('id_password2')
        pw2_field.clear()
        pw2_field.send_keys(pw2)
        otp_field = form.find_element_by_id('id_otp')
        otp_field.clear()
        otp_field.send_keys(otp)
        form.find_element_by_css_selector('button[type="submit"]').click()

    def _fill_form_step2_different_passwords(self):
        """
        With different passwords
        """
        self.__fill_step2_form('R3llyAG00DP4$&w0Rd_!', 'Bu10nlYPa55w0RD_1S_Good!',
                               RegistrationRoundTripTest.__get_valid_otp())
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _fill_form_step2_too_short_passwords(self):
        """
        With too short passwords
        """
        self.__fill_step2_form('$h0R+', '$h0R+',
                               RegistrationRoundTripTest.__get_valid_otp())
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _fill_form_step2_too_easy_passwords(self):
        """
        With too easy passwords
        """
        self.__fill_step2_form('test1234', 'test1234',
                               RegistrationRoundTripTest.__get_valid_otp())
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _fill_form_step2_too_username_like_passwords(self):
        """
        With too easy passwords
        """
        self.__fill_step2_form('test_user1', 'test_user1',
                               RegistrationRoundTripTest.__get_valid_otp())
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _fill_form_step2_all_numeric_passwords(self):
        """
        With all numeric passwords
        """
        self.__fill_step2_form('1357111319', '1357111319',
                               RegistrationRoundTripTest.__get_valid_otp())
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _fill_form_step2_bad_otp(self):
        """
        With bad otp
        """
        self.__fill_step2_form('R3llyAG00DP4$&w0Rd_!', 'R3llyAG00DP4$&w0Rd_!', 'WR0NG1')
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _fill_form_step2_wrong_otp(self):
        """
        With wrong otp
        """
        self.__fill_step2_form('R3llyAG00DP4$&w0Rd_!', 'R3llyAG00DP4$&w0Rd_!',
                               RegistrationRoundTripTest.__get_invalid_otp())
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _fill_form_step2_with_valid_data(self):
        """
        With valid data
        """
        self.__fill_step2_form('R3llyAG00DP4$&w0Rd_!', 'R3llyAG00DP4$&w0Rd_!',
                               RegistrationRoundTripTest.__get_valid_otp())
        self.assertTrue(str(self.webdriver.current_url).endswith('/register/step-2'))

    def _check_success(self):
        """
        Check if the registration is finished
        """
        # web page
        success_message = self.webdriver.find_element_by_css_selector('div.card-body h2')
        self.assertEqual('Ready to go!', success_message.text.strip())
        # backend
        self.assertEqual(0, PendingRegistration.objects.all().count())
        user = authenticate(  # nosec
            username='test_user',
            password='R3llyAG00DP4$&w0Rd_!',
            one_time_pw=self.__get_valid_otp()
        )
        self.assertIsNotNone(user)

    def _check_link_now_invalid(self, link):
        """
        Check if the link is now invalid
        """

    def test_roundtrip(self):
        """
        Roundtrip cook book
        """
        self._begin_registration()
        self._fill_form_step1_existing_user()
        self._fill_form_step1_bad_email()
        self._fill_form_step1_empty_first_name()
        self._fill_form_step1_all_wrong()
        self._fill_form_step1_with_valid_data()
        next_url = self._check_mail()
        self._begin_step2(next_url)
        self._fill_form_step2_different_passwords()
        self._fill_form_step2_too_short_passwords()
        self._fill_form_step2_too_easy_passwords()
        self._fill_form_step2_too_easy_passwords()
        self._fill_form_step2_too_username_like_passwords()
        self._fill_form_step2_all_numeric_passwords()
        self._fill_form_step2_bad_otp()
        self._fill_form_step2_wrong_otp()
        self._fill_form_step2_with_valid_data()
        self._check_success()
        self._check_link_now_invalid(next_url)

    def test_happy_path(self):
        """
        Test the happy path registration, without any errors
        """
        self._begin_registration()
        self._fill_form_step1_with_valid_data()
        next_url = self._check_mail()
        self._begin_step2(next_url)
        self._fill_form_step2_with_valid_data()
        self._check_success()
        self._check_link_now_invalid(next_url)


class RegistrationUnfriendlyRequestsTest(TestCase):
    """
    Torture the registration view
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = HubUser.objects.create_user(username='only_for_reg_test')  # type: HubUser
        cls.pend_reg = PendingRegistration.objects.create(user=cls.user)  # type: PendingRegistration

    def test_step2_bad_get_parameters(self):
        """
        Test with bad links of all kind
        """
        good_uuid = str(uuid4())
        nice_key = '1_1234567890_1_1234567890_1_1234567890_1_1234567890_1_1234567890_1' \
                   'a_BCDEFGHIJK_a_BCDEFGHIJK_a_BCDEFGHIJK_a_BCDEFGHIJK_a_BCDEFGHIJK_a' \
                   'x_abcdefghij_x_abcdefghij_x_abcdefghij_x_abcdefghij_x_abcdefghij_x' \
                   '0_0000000000_0_0000000000_0_0000000000_0_0000000000_0_0000000000_0' \
                   '-_----------_-_----------_-_----------_-_----------_-_----------_-'
        signed_key = Signer(salt=good_uuid).sign(nice_key)
        signed_key_matching = Signer(salt=str(self.pend_reg.uuid)).sign(nice_key)
        test_items = (
            # reg, key
            (None, None),
            (None, 'OhMyKeyThere'),
            (str(uuid4()), None),
            (str(uuid4()), 'OhMyKeyThere'),
            (str(uuid4()), nice_key),
            (good_uuid, signed_key),
            (None, signed_key),
            (str(uuid4()), signed_key),
            (str(self.pend_reg.uuid), signed_key),
            (str(self.pend_reg.uuid), signed_key_matching),
        )
        for reg, key in test_items:
            with self.subTest(msg='Testing reg={} and key={}'.format(reg, key)):
                url = '/hub/register/step-2'
                parameters = {}
                if reg is not None:
                    parameters['reg'] = reg
                if key is not None:
                    parameters['key'] = key
                response = self.client.get(url, data=parameters)
                self.assertTrue('<h2>Ooh ooh...</h2>' in response.content.decode('utf-8'))

    def test_with_defective_session(self):
        """
        Test with defective session data
        """
        reg = str(self.pend_reg.uuid)
        key = Signer(salt=reg).sign(self.pend_reg.key)
        test_items = (
            # pw, otp, reg, key
            ('reallyC0olPa$$_w0RD!', get_otp(self.user.get_totp_secret()), reg, key),
            ('reallyC0olPa$$_w0RD!', get_otp(self.user.get_totp_secret()), reg, key + 'x'),
            ('reallyC0olPa$$_w0RD!', get_otp(self.user.get_totp_secret()), str(uuid4()), key),
        )
        for password, otp, reg, key in test_items:
            with self.subTest(msg='Testing with password={}, otp={}, reg={}, key={}'.format(password, otp, reg, key)):
                response = self.client.post('/hub/register/step-2', data={
                    'reg': reg,
                    'key': key,
                    'password1': password, 'password2': password,
                    'otp': otp
                })
                self.assertTrue('<h2>Ooh ooh...</h2>' in response.content.decode('utf-8'))
