"""
Tests for the otp template tags
"""
from base64 import b32encode

from django.test import SimpleTestCase

from hub_app.templatetags.hub_app_otp import do_inline_otp_qr_code


class InlineQrCodeTest(SimpleTestCase):
    """
    Test the inline QR Code Tag
    """

    def test_context(self):
        """
        Test the context
        """
        context = do_inline_otp_qr_code('test_user', b32encode(b'ThisIsJustATestSecretForASimpleUnitTestHere'))
        self.assertIsInstance(context, dict)
        self.assertIn('qr_img_data', context)
        self.assertIsInstance(context.get('qr_img_data'), str)
        self.assertTrue(context.get('qr_img_data').startswith('data:image/png;base64,'))
