"""
Test the OTP validation
"""
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from hub_app.authlib.totp.validators import OtpValidator


class OtpValidationTest(SimpleTestCase):
    """
    Very basic tests
    """

    def test_good_ones(self):
        """
        Test good OTPs
        """
        test_items = (
            '000000', '111111', '222222', '333333', '444444', '555555', '666666', '777777', '888888', '999999',
            '123456', '654321', '012345', '543210',
        )
        for test_item in test_items:
            with self.subTest(msg='Testing good "{}"'.format(test_item)):
                result = OtpValidator()(test_item)
                self.assertIsNone(result)

    def test_bad_ones(self):
        """
        Test bad OTPs
        """
        test_items = (
            None, '', '1', '22', '333', '4444', '55555', '7777777', '88888888', '999999999',
            'abcdef', '12ab56', 'AB12CD', '-12345', '-123456',
        )
        for test_item in test_items:
            with self.subTest('Testing bad "{}"'.format(test_item)):
                self.assertRaisesMessage(
                    ValidationError,
                    'Only numbers allowed.',
                    OtpValidator(),
                    test_item
                )
