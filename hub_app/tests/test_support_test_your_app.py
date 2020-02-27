"""
Test the "Test your App" View
"""
from django.test import TestCase
from django.urls import reverse


class TestYourAppTest(TestCase):
    """
    Simple Smoke Test
    """

    url = reverse('ha:supp:test-your-app')

    def test_smoke(self):
        """
        Just use the view
        """
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        test_items = (
            '', ' ', '      ', 'aaaaaa', 'a1b2c3', '123456', '987654', '000000', '-10000', '-123456'
        )
        for test_item in test_items:
            with self.subTest(msg='Testing with "{}"'.format(test_item)):
                response = self.client.post(self.url, data={
                    'otp_to_be_tested': test_item
                })
                self.assertEqual(200, response.status_code)
