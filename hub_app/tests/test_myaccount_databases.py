"""
MyAccount Databases Test
"""
from django.urls import reverse

from hub_app.tests.test_myaccount import MyAccountTest


class DatabasesPageTest(MyAccountTest):
    """
    Check access to the databases page
    """

    url = reverse('ha:acc:databases')
