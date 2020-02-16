"""
Tests for all cases of the Unique Username Validator
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from hub_app.models import HubUser
from hub_app.reglib.validators import validate_unique_username


class UniqueUsernameValidatorTest(TestCase):
    """
    Test with a user in DB
    """

    @classmethod
    def setUpTestData(cls):
        cls.existing_user = HubUser.objects.create(username='i_am_already_there')

    def test_syntax_unavailable_usernames(self):
        """
        Test Username that must fail because they are not comparable
        """
        test_names = (
            '  a  ', '    ', '   ', '  ', ' ', ' ab ',
            None, ['a'], [], {'user': 'A'}, {},
        )
        for test_name in test_names:
            with self.subTest(msg='Testing username "{}"'.format(test_name)):
                self.assertRaisesMessage(
                    ValidationError,
                    'This username is currently not available',
                    validate_unique_username,
                    test_name
                )

    def test_already_taken_username(self):
        """
        Test variants of the taken username
        """
        test_names = (
            'i_am_already_there', 'I_Am_Already_There', 'I_AM_ALREADY_THERE', 'i_aM_aLReAdY_thErE',
            ' i_am_already_there', '  I_Am_Already_There', '   I_AM_ALREADY_THERE', '    i_aM_aLReAdY_thErE',
            'i_am_already_there ', 'I_Am_Already_There  ', 'I_AM_ALREADY_THERE   ', 'i_aM_aLReAdY_thErE    ',
            '    i_am_already_there ', '   I_Am_Already_There  ', '  I_AM_ALREADY_THERE   ', ' i_aM_aLReAdY_thErE    ',
        )
        for test_name in test_names:
            with self.subTest(msg='Testing username "{}"'.format(test_name.replace(' ', '[blank]'))):
                self.assertRaisesMessage(
                    ValidationError,
                    '"{}" is currently not available'.format(test_name),
                    validate_unique_username,
                    test_name
                )

    def test_not_taken_username(self):
        """
        Test not taken usernames
        """
        test_names = (
            'test', ' test', '  test', '    test',
            ' test ', 'test  ', '  test  ', '    test   ',
        )
        for test_name in test_names:
            with self.subTest(msg='Testing username "{}"'.format(test_name.replace(' ', '[blank]'))):
                self.assertIsNone(validate_unique_username(test_name))
