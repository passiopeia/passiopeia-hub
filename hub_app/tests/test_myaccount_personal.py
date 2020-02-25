"""
MyAccount Personal Test
"""
import re
from urllib.parse import unquote
from uuid import uuid4

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage
from django.core.signing import Signer
from django.urls import reverse
from urllib3.util import parse_url

from hub_app.accountlib.email import get_email_key
from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser, PendingEMailChange
from hub_app.tests.test_myaccount import MyAccountTest


class PersonalPageTest(MyAccountTest):
    """
    Check access to the personal data page
    """

    url = reverse('ha:acc:personal')


class PersonalNamePageTest(MyAccountTest):
    """
    Check Name Changing
    """

    url = reverse('ha:acc:personal.name')

    def _compare(self, first, last):
        """
        Compare first and last name
        """
        user = HubUser.objects.get(id=self.normal_user.id)
        self.assertEqual(first, user.first_name)
        self.assertEqual(last, user.last_name)

    def test_round_trip(self):
        """
        Test a round trip
        """
        self.client.login(username=self.normal_user.username, password=self.password, one_time_pw=get_otp(self.secret))
        self._open()
        current_first = self.normal_user.first_name
        current_last = self.normal_user.last_name
        wrong_data = (
            # first_name, last_name
            ('', ''),
            ('', 'Drebin')
        )
        for first, last in wrong_data:
            with self.subTest(msg='Testing bad first_name="{}", last_name="{}"'.format(first, last)):
                response = self.client.post(self.url, {'first_name': first, 'last_name': last})
                self.assertEqual(200, response.status_code)
                self._compare(current_first, current_last)
        good_data = (
            # first_name, last_name
            ('Frank', 'Drebin'),
            ('A', 'Men'),
            ('A', ''),
            ('Frank', ''),
            ('Frank', 'Summerland'),
        )
        for first, last in good_data:
            with self.subTest(msg='Testing good first_name="{}", last_name="{}"'.format(first, last)):
                response = self.client.post(self.url, {'first_name': first, 'last_name': last})
                self.assertEqual(200, response.status_code)
                self._compare(first, last)


class PersonalEMailPageTest(MyAccountTest):
    """
    Test the E-Mail-Address Changing
    """

    url = reverse('ha:acc:personal.email')

    def test_round_trip(self):
        """
        Test the complete round trip
        """
        self.client.login(username=self.normal_user.username, password=self.password, one_time_pw=get_otp(self.secret))
        self._open()
        current_email = self.normal_user.email
        new_email = 'it.looks@right.org'
        wrong_data = (
            # email
            '', '  ', 'doo@', '@doo', 'doo@doo@doo', 'doo@@doo.de', 'doo@doo..ad', 'doo@doo.', '.doo@doo.de',
            'doo@doo.de.', '.doo#doo@doo.de', '?.@doo.de'
        )
        for email in wrong_data:
            with self.subTest(msg='Testing with bad e-mail "{}"'.format(email)):
                response = self.client.post(self.url, data={
                    'new_email': email
                }, follow=False)
                self.assertEqual(0, PendingEMailChange.objects.count())
                self.assertEqual(200, response.status_code)
                self.assertEqual(0, len(mail.outbox))
                self.assertEqual(current_email, HubUser.objects.get(id=self.normal_user.id).email)
        with self.subTest('Now with a good e-mail address'):
            response = self.client.post(self.url, data={
                'new_email': new_email
            }, follow=False)
            self.assertEqual(200, response.status_code)
            self.assertEqual(new_email, PendingEMailChange.objects.first().new_email)
            self.assertEqual(1, len(mail.outbox))
            self.assertEqual(current_email, HubUser.objects.get(id=self.normal_user.id).email)
            self.assertEqual(1, PendingEMailChange.objects.count())
        more_tries = (
            'good.one@test.org', 'better.one@test.de', 'but.3@three.org'
        )
        for good in more_tries:
            with self.subTest('Now more good ones that get rejected: "{}"'.format(good)):
                self._open()
                response = self.client.post(self.url, data={
                    'new_email': good
                }, follow=False)
                self.assertEqual(1, len(mail.outbox))
                self.assertEqual(1, PendingEMailChange.objects.count())
                self.assertEqual(200, response.status_code)
                self.assertEqual(current_email, HubUser.objects.get(id=self.normal_user.id).email)
                self.assertEqual(new_email, PendingEMailChange.objects.first().new_email)
        with self.subTest(msg='Checking E-Mail'):
            confirm_mail = mail.outbox[0]  # type: EmailMessage
            self.assertEqual(settings.EMAIL_VERIFICATION_SUBJECT, confirm_mail.subject)
            self.assertEqual(settings.EMAIL_VERIFICATION_FROM, confirm_mail.from_email)
            self.assertEqual([new_email], confirm_mail.to)
            self.assertTrue('Hi Frank!' in str(confirm_mail.body))
            extract_link_regex = re.compile(r'.*(?P<url>http(s)?://.*/personal/email/.*?)\s.*',
                                            re.MULTILINE | re.UNICODE | re.DOTALL)
            match = extract_link_regex.match(str(confirm_mail.body))
            self.assertIsNotNone(match)
            next_link = match.group('url')
            self.assertIsNotNone(next_link)
        uuid = str(PendingEMailChange.objects.first().uuid)
        bad_links = (
            reverse('ha:acc:personal.email.verify', kwargs={
                'change': uuid
            }) + '?change_key=Moeoeoeb',
            reverse('ha:acc:personal.email.verify', kwargs={
                'change': uuid
            }) + '?change_key=IsVeryLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong'
                 'LongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong'
                 'LongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong',
            reverse('ha:acc:personal.email.verify', kwargs={
                'change': str(uuid4())
            }) + '?change_key=IsVeryLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong'
                 'LongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong'
                 'LongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong',
            reverse('ha:acc:personal.email.verify', kwargs={
                'change': str(uuid4())
            }) + '?no_change_key=IsVeryLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong'
                 'LongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong'
                 'LongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLongLong',
        )
        for bad_link in bad_links:
            with self.subTest(msg='Call bad link "{}"'.format(bad_link)):
                response = self.client.get(bad_link, follow=False)
                self.assertEqual(200, response.status_code)
                self.assertIn('This link seems to be invalid.', response.content.decode('utf-8'))
        with self.subTest(msg='Call next link "{}"'.format(next_link)):
            response = self.client.get(next_link, follow=False)
            self.assertEqual(200, response.status_code)
            self.assertIn('click the following button to confirm', response.content.decode('utf-8'))
        with self.subTest(msg='Check if database is still OK'):
            self.assertEqual(1, PendingEMailChange.objects.count())
            self.assertEqual(new_email, PendingEMailChange.objects.first().new_email)
            self.assertEqual(1, len(mail.outbox))
            self.assertEqual(current_email, HubUser.objects.get(id=self.normal_user.id).email)
        bad_uuid = str(uuid4())
        bad_confirms = (
            # uuid, change_key
            (uuid, ''),
            (uuid, 'bad_key'),
            (bad_uuid, ''),
            (bad_uuid, 'bad_key'),
            (uuid, Signer(salt=uuid).sign(get_email_key())),
            (bad_uuid, Signer(salt=bad_uuid).sign(get_email_key())),
            (uuid, Signer(salt='01').sign(get_email_key())),
            (bad_uuid, Signer(salt='12').sign(get_email_key())),
        )
        for bad_uuid, bad_change_key in bad_confirms:
            with self.subTest('Testing failing confirmation with UUID="{}" and change_key="{}"'.format(
                    bad_uuid, bad_change_key
            )):
                response = self.client.post(reverse('ha:acc:personal.email.verify', kwargs={
                    'change': bad_uuid
                }), data={
                    'change_key': bad_change_key
                }, follow=False)
                self.assertEqual(200, response.status_code)
                self.assertEqual(current_email, HubUser.objects.get(id=self.normal_user.id).email)
                self.assertEqual(1, PendingEMailChange.objects.count())
                self.assertEqual(new_email, PendingEMailChange.objects.first().new_email)
                self.assertEqual(1, len(mail.outbox))
        with self.subTest(msg='Confirming'):
            url_parts = parse_url(next_link)
            end_point = url_parts.path
            confirm_key = unquote(url_parts.query[11:])
            response = self.client.post(end_point, {
                'change_key': confirm_key
            }, follow=False)
            self.assertEqual(200, response.status_code)
            self.assertIn('Your E-Mail Address has been verified.', response.content.decode('utf-8'))
            self.assertEqual(0, PendingEMailChange.objects.count())
            self.assertEqual(new_email, HubUser.objects.get(id=self.normal_user.id).email)
