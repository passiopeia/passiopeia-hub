"""
Test the Template Tag that produces the Admin Link
"""
from bs4 import BeautifulSoup
from bs4.element import PageElement
from django.test import TestCase

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser


class AdminButtonTemplateTagTest(TestCase):
    """
    Test the template tag
    """

    @classmethod
    def setUpTestData(cls):
        cls.secret = b'ThisIsJustForThisTestAndNotAVerySecureSecret.But_OK4Y_4n0w'
        cls.normal_user = HubUser.objects.create_user(username='normal', password='P4ssw0rd!')  # nosec
        cls.staff_user = HubUser.objects.create_user(username='staff', password='P4ssw0rd!', is_staff=True)  # nosec
        cls.admin_user = HubUser.objects.create_superuser(username='admin', password='P4ssw0rd!')  # nosec
        for user in [cls.normal_user, cls.staff_user, cls.admin_user]:
            user.set_totp_secret(cls.secret)
            user.save()

    def __get_admin_switch(self) -> PageElement:
        """
        Get the Admin Switch
        """
        response = self.client.get('/', follow=True)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find('a', attrs={
            'data-ui-relevance': 'admin-switch'
        })  # type: PageElement
        return soup

    def __login(self, user: HubUser):
        """
        Log a user in
        """
        res = self.client.login(username=user.username, password='P4ssw0rd!', one_time_pw=get_otp(self.secret))  # nosec
        self.assertTrue(res)

    def __check_button_config(self, button: PageElement):
        """
        Check the button
        """
        self.assertIsNotNone(button)
        self.assertEqual('/admin/', button['href'])

    def test_anonymous(self):
        """
        Test with an anonymous user
        """
        self.assertIsNone(self.__get_admin_switch())

    def test_normal_user(self):
        """
        Test with a normal user
        """
        self.__login(self.normal_user)
        self.assertIsNone(self.__get_admin_switch())

    def test_staff_user(self):
        """
        Test with a staff user
        """
        self.__login(self.staff_user)
        self.__check_button_config(self.__get_admin_switch())

    def test_super_user(self):
        """
        Test with a staff user
        """
        self.__login(self.admin_user)
        self.__check_button_config(self.__get_admin_switch())
