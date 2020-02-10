"""
Testing the Symmetric Crypt Methods
"""
from django.test import SimpleTestCase

from hub_app.authlib.crypt import SymmetricCrypt


class SymmetricCryptTest(SimpleTestCase):
    """
    Simple Smoke test for the symmetric cryp
    """

    def test_in_out(self):
        """
        Simply encrypt and decrypt
        """
        test_items = (
            b'DSJFBSHDFBSMDBFMJERFSMDNBVMSESjhdfkshdfhjkeskjedfnskdj',
            b'SUPER-SECRET-SUPER-SECRET-MEGA-SECRET-MORE-SECRET-EVEN-MORE',
            b'JustAString',
        )
        for test_item in test_items:
            with self.subTest(msg='Testing with "{}"'.format(test_item)):
                encrypted_test_item = SymmetricCrypt().encrypt(test_item)
                decrypted_test_item = SymmetricCrypt().decrypt(encrypted_test_item)
                self.assertEqual(test_item, decrypted_test_item)
                self.assertNotEqual(test_item, encrypted_test_item)
                self.assertIsNotNone(encrypted_test_item)
                self.assertIsNotNone(decrypted_test_item)
