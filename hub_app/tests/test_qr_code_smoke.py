"""
Simple Smoke Tests for the QR code generator
"""
from base64 import b32encode

from django.test import SimpleTestCase
from qrcode.image.base import BaseImage
from qrcode.image.pil import PilImage
from qrcode.image.svg import SvgPathImage, SvgPathFillImage

from hub_app.authlib.totp.qr import create_transparent_svg_qr_code, create_png_qr_code, create_svg_qr_code


class QrCodeGenerationSmokeTest(SimpleTestCase):
    """
    Test the QR Code generation
    """

    def test_image_generation_method(self):
        """
        Test all factories
        """
        test_items = (
            (create_transparent_svg_qr_code, SvgPathImage),
            (create_svg_qr_code, SvgPathFillImage),
            (create_png_qr_code, PilImage),
        )
        for func, concrete_type in test_items:
            with self.subTest(msg='Testing with method "{}" for an image of type "{}'.format(func, concrete_type)):
                img = func('test_user', b32encode(b'SOME-EASY-TEST-DATA-WITH-SOME-BYTES-OF-LENGTH-HOW-COOL-THIS-IS!'))
                self.assertIsNotNone(img)
                self.assertIsInstance(
                    img,
                    BaseImage
                )
                self.assertIsInstance(
                    img,
                    concrete_type
                )
