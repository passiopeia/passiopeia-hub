"""
Tests for the "cleanburnedotp" command
"""
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, tag
from django.utils.timezone import now

from hub_app.management.commands import cleanburnedotp
from hub_app.models import HubUser, BurnedOtp


class CleanUpBurnedOtpTest(TestCase):
    """
    Clean the Database Test
    """

    @classmethod
    def setUpTestData(cls):
        current_time = now()
        cls.user = HubUser.objects.create(
            username='mr_test_burned_otp'
        )
        cls.burned = []
        for i, minutes in enumerate([1, 5, 59, 60, 61, 119, 120, 121, 240, 9999, 99999, 899999]):
            cls.burned.append(str(BurnedOtp.objects.create(
                user=cls.user,
                token=str(100000 + i),
                burned_timestamp=current_time - timedelta(minutes=minutes)
            ).uuid))
        with StringIO() as out:
            call_command(cleanburnedotp.Command(), stdout=out)

    def test_burned_otp_exists(self):
        """
        Test OTPs that should still exist
        """
        test_indexes = (0, 1, 2, 3, 4, 5)
        for test_index in test_indexes:
            with self.subTest('Testing if index "{}" is not deleted'.format(test_index)):
                burned_otp = BurnedOtp.objects.get(uuid=self.burned[test_index])
                self.assertIsNotNone(burned_otp)
                self.assertEqual(self.user, burned_otp.user)
                self.assertEqual(str(100000 + test_index), burned_otp.token)

    def test_burned_otp_is_deleted(self):
        """
        Test OTPs that should be deleted
        """
        test_indexes = (6, 7, 8, 9, 10, 11)
        for test_index in test_indexes:
            with self.subTest('Testing if index "{}" is deleted'.format(test_index)):
                self.assertRaises(
                    BurnedOtp.DoesNotExist,
                    BurnedOtp.objects.get,
                    uuid=self.burned[test_index]
                )


class DeleteOnEmptyDatabaseTest(TestCase):
    """
    Run on an empty database
    """

    def test_delete_on_empty(self):
        """
        We are expecting no exception
        """
        with StringIO() as out:
            call_command(cleanburnedotp.Command(), stdout=out)
            self.assertRegex(out.getvalue().strip(), r'(Done).{0,10}$')


@tag('slow')
class MassDeletionTest(TestCase):
    """
    Mass Deletion Test
    """

    @classmethod
    def setUpTestData(cls):
        cls.kick_time = now() - timedelta(minutes=240)
        cls.user = HubUser.objects.create(
            username='mr_test_otp_mass_deletion'
        )

    def test_mass_deletion(self):
        """
        Test Mass Deletion
        """
        number_of_otps_to_be_tested = (100, 1000, 5000, 10000, 50000)
        for number_of_otps in number_of_otps_to_be_tested:
            with self.subTest(msg='Testing with {} OTPs'.format(number_of_otps)):
                for i in range(number_of_otps):
                    BurnedOtp.objects.create(
                        user=self.user,
                        token=str(100000 + i),
                        burned_timestamp=self.kick_time - timedelta(seconds=i)
                    )
                self.assertEqual(
                    number_of_otps,
                    BurnedOtp.objects.count()
                )
                with StringIO() as out:
                    call_command(cleanburnedotp.Command(), stdout=out)
                    self.assertRegex(out.getvalue().strip(), r'(Done).{0,10}$')
                self.assertEqual(
                    0,
                    BurnedOtp.objects.count()
                )
