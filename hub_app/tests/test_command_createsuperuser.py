"""
Test Suite for the 'createsuperuser' command
"""
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from hub_app.management.commands import createsuperuser
from hub_app.models import HubUser


class CreateSuperUserFromCommandLineTest(TestCase):
    """
    Test the creation of a SuperUser from the Command Line
    """

    @classmethod
    def setUpTestData(cls):
        cls.existing_superuser = HubUser.objects.create_user(  # nosec
            username='test_user_that_exists',
            password='0nLiF4outS0meTe$ting'
        )

    def test_good_case(self):
        """
        Test positive case
        """
        with StringIO() as out:
            call_command(  # nosec
                createsuperuser.Command(),
                username='test@test.org',
                password='12Test34$56oO.',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )
            self.assertRegex(
                out.getvalue(),
                r'(Superuser\s"test@test\.org"\screated\ssuccessfully).{0,10}$'
            )
        obj = HubUser.objects.get(username='test@test.org')  # type: HubUser
        self.assertTrue(obj.is_active)
        self.assertTrue(obj.is_superuser)
        self.assertTrue(obj.is_staff)

    def test_bad_cases(self):
        """
        Test bad cases
        """
        test_items = (
            # case, user, pass, secret
            ('Empty Username',
             '', 'W3ryG0oDPA5sWOrd', 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('Empty Password',
             'test1', '', 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('Empty Secret',
             'test2', 'W3ryG0oDPA5sWOrd', ''),
            ('Empty Username and empty Password',
             '', '', 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('Empty Username, empty Password and empty Secret',
             '', '', ''),
            ('Too short secret',
             'test3', 'W3ryG0oDPA5sWOrd', 'SUPERSECRETSUPER'),
            ('Invalid secret',
             'test4', 'W3ryG0oDPA5sWOrd', '1234SUPERSECRETSUPER'),
            ('Password too short',
             'test5', 'W3rWOrd', 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('Password only numbers',
             'test6', '1234123499', 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('Password too common',
             'test7', 'testtest', 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('None Username',
             None, 'W3ryG0oDPA5sWOrd', 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('None Password',
             'test8', None, 'SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER'),
            ('None Secret',
             'test9', 'W3ryG0oDPA5sWOrd', None),
        )
        for test_case, username, password, secret in test_items:
            with self.subTest(msg='Testing case "{}"'.format(test_case)), StringIO() as out:
                self.assertRaises(  # nosec
                    CommandError,
                    call_command,
                    createsuperuser.Command(),
                    username=username,
                    password=password,
                    secret=secret,
                    stdout=out
                )
                self.assertEqual(1, HubUser.objects.count())

    def test_duplicate(self):
        """
        Try to create a duplicate
        """
        with StringIO() as out:
            self.assertRaisesRegex(  # nosec
                CommandError,
                r'(The\suser\s"test_user_that_exists"\salready\sexists\.).{0,10}$',
                call_command,
                createsuperuser.Command(),
                username='test_user_that_exists',
                password='12Test34$56oO.',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )


class CreateSuperUserFromUserInputTest(TestCase):
    """
    Create a superuser with user input
    """

    @patch('hub_app.management.commands.createsuperuser.get_input', return_value='test-user1')
    def test_good_case_username(self, _):
        """
        Test the good case with username
        """
        with StringIO() as out:
            call_command(  # nosec
                createsuperuser.Command(),
                password='12Test34$56oO.',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )
            self.assertRegex(
                out.getvalue(),
                r'(Superuser\s"test-user1"\screated\ssuccessfully).{0,10}$'
            )
        obj = HubUser.objects.get(username='test-user1')  # type: HubUser
        self.assertIsNotNone(obj)

    @patch('hub_app.management.commands.createsuperuser.get_input',
           return_value='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER')
    def test_good_case_secret(self, _):
        """
        Test the good case with secret
        """
        with StringIO() as out:
            call_command(  # nosec
                createsuperuser.Command(),
                username='test-user2',
                password='12Test34$56oO.',
                stdout=out
            )
            self.assertRegex(
                out.getvalue(),
                r'(Superuser\s"test-user2"\screated\ssuccessfully).{0,10}$'
            )
            obj = HubUser.objects.get(username='test-user2')  # type: HubUser
            self.assertIsNotNone(obj)

    @patch('hub_app.management.commands.createsuperuser.get_masked_input', return_value='12Test34$56oO.')
    def test_good_case_password(self, _):
        """
        Test the good case with password
        """
        with StringIO() as out:
            call_command(  # nosec
                createsuperuser.Command(),
                username='test-user3',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )
            self.assertRegex(
                out.getvalue(),
                r'(Superuser\s"test-user3"\screated\ssuccessfully).{0,10}$'
            )
        obj = HubUser.objects.get(username='test-user3')  # type: HubUser
        self.assertIsNotNone(obj)

    @patch('hub_app.management.commands.createsuperuser.get_masked_input', return_value='12Test34$56oO.')
    @patch('hub_app.management.commands.createsuperuser.get_input', return_value='test-user4')
    def test_good_case_username_and_password(self, *_):
        """
        Test the good case with username and password
        """
        with StringIO() as out:
            call_command(  # nosec
                createsuperuser.Command(),
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )
            self.assertRegex(
                out.getvalue(),
                r'(Superuser\s"test-user4"\screated\ssuccessfully).{0,10}$'
            )
        obj = HubUser.objects.get(username='test-user4')  # type: HubUser
        self.assertIsNotNone(obj)

    @patch('hub_app.management.commands.createsuperuser.get_input', return_value='')
    def test_bad_case_empty_username(self, _):
        """
        Test bad case with an empty username
        """
        with StringIO() as out:
            self.assertRaises(  # nosec
                CommandError,
                call_command,
                createsuperuser.Command(),
                password='12Test34$56oO.',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )

    @patch('hub_app.management.commands.createsuperuser.get_input', return_value='')
    def test_bad_case_empty_secret(self, _):
        """
        Test bad case with an empty secret
        """
        with StringIO() as out:
            self.assertRaises(  # nosec
                CommandError,
                call_command,
                createsuperuser.Command(),
                username='test-user7',
                password='12Test34$56oO.',
                stdout=out
            )

    @patch('hub_app.management.commands.createsuperuser.get_masked_input', return_value='')
    def test_bad_case_empty_password(self, _):
        """
        Test bad case with an empty password
        """
        with StringIO() as out:
            self.assertRaises(  # nosec
                CommandError,
                call_command,
                createsuperuser.Command(),
                username='test-user8',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )

    @patch('hub_app.management.commands.createsuperuser.get_input', return_value=None)
    def test_bad_case_none_username(self, _):
        """
        Test bad case with an none username
        """
        with StringIO() as out:
            self.assertRaises(  # nosec
                CommandError,
                call_command,
                createsuperuser.Command(),
                password='12Test34$56oO.',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )

    @patch('hub_app.management.commands.createsuperuser.get_input', return_value=None)
    def test_bad_case_none_secret(self, _):
        """
        Test bad case with an none secret
        """
        with StringIO() as out:
            self.assertRaises(  # nosec
                CommandError,
                call_command,
                createsuperuser.Command(),
                username='test-user7',
                password='12Test34$56oO.',
                stdout=out
            )

    @patch('hub_app.management.commands.createsuperuser.get_masked_input', return_value=None)
    def test_bad_case_none_password(self, _):
        """
        Test bad case with an none password
        """
        with StringIO() as out:
            self.assertRaises(  # nosec
                CommandError,
                call_command,
                createsuperuser.Command(),
                username='test-user8',
                secret='SUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPERSUPERSECRETSUPER',
                stdout=out
            )
