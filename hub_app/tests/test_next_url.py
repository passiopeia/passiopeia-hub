"""
Tests for the navlib next-url handling
"""
from bs4 import BeautifulSoup
from django.test import SimpleTestCase, RequestFactory, TestCase

from hub_app.authlib.totp.token import get_otp
from hub_app.models import HubUser
from hub_app.navlib.next_url import get_next, _get_next


class NavLibNextUrlTest(SimpleTestCase):
    """
    Tests for the Nav Lib / next_url handling
    """

    def setUp(self) -> None:
        self.request_factory = RequestFactory()

    def test(self):
        """
        Test valid and invalid combinations
        """
        factory_methods = (
            ('GET', self.request_factory.get),
            ('POST', self.request_factory.post),
        )
        test_items = (
            # next_element, expectation
            ('', None),
            ('null', None),
            ('https://passiopeia.github.io/', None),
            ('/a/b/c', '/a/b/c'),
            ('/a/b/c?next=/d/e/f', '/a/b/c?next=/d/e/f'),
            ('login?next=test', None),
            ([''], None),
            (['null'], None),
            (['https://passiopeia.github.io/'], None),
            (['/a/b/c'], '/a/b/c'),
            (['/a/b/c?next=/d/e/f'], '/a/b/c?next=/d/e/f'),
            (['login?next=test'], None),
            (['', '/a/b/c'], None),
            (['/a/b/c', ''], '/a/b/c'),
            (['https://passiopeia.github.io/', '/a/b/c', ''], None),
        )
        for method, factory in factory_methods:
            for next_part, expectation in test_items:
                with self.subTest(
                        msg='Testing {} with next parameter "{}", expecting "{}"'.format(method, next_part, expectation)
                ):
                    request = factory('/hub/auth/login', data={
                        'next': next_part
                    })
                    self.assertEqual(expectation, get_next(request))

    def test_corner_case_leading_none(self):
        """
        Test corner cases with a leading None
        """
        test_items = (
            [None],
            [None, 'str'],
            [None, '/str'],
            [None, '/str', None],
            [None, None, None],
        )
        for test_item in test_items:
            with self.subTest(msg='Checking "{}"'.format(test_item)):
                self.assertIsNone(_get_next(test_item))

    def test_corner_case_trailing_none(self):
        """
        Test corner cases with a trailing None
        """
        test_items = (
            ['/str', None],
            ['/str', None, None],
            ['/str_a/', None, '/str'],
            ['/str_a/', None, '/str', None],
        )
        for test_item in test_items:
            with self.subTest(msg='Checking "{}"'.format(test_item)):
                self.assertIsNotNone(_get_next(test_item))


class NextUrlInLoginFormTest(TestCase):
    """
    Test if the form works with next parameters
    """

    username = 'test_redirect_user'
    password = 'R3D1rect-Passw0rd'  # nosec
    secret = b'bThisIsOnlyATestSecretPleaseNeverUseThisOneInProduction!'

    next_url = '/this/is/the/redirect/target'

    @classmethod
    def setUpTestData(cls):
        cls.user = HubUser.objects.create_user(
            username=cls.username,
            password=cls.password,
        )  # type: HubUser
        cls.user.set_totp_secret(cls.secret)
        cls.user.save()

    def _check_next_url_in_source(self, content):
        """
        Check the input tag
        """
        soup = BeautifulSoup(content.decode('utf-8'), 'html.parser').find('form', attrs={
            'data-ui-relevance': 'main-login'
        }).find_next('input', attrs={
            'type': 'hidden',
            'data-ui-relevance': 'next-url-tag',
            'name': 'next'
        })
        self.assertEqual(self.next_url, soup['value'])

    def test_with_next(self):
        """
        Test with existing "next"
        """
        response = self.client.get('/hub/auth/login', data={
            'next': self.next_url
        }, follow=True)
        self.assertEqual(200, response.status_code)
        self._check_next_url_in_source(response.content)
        response = self.client.post('/hub/auth/login', data={
            'username': 'something',
            'password': 'passsssw0rd!',
            'otp': '123456',
            'next': self.next_url
        }, follow=True)
        self.assertEqual(200, response.status_code)
        self._check_next_url_in_source(response.content)
        response = self.client.post('/hub/auth/login', data={
            'username': self.username,
            'password': self.password,
            'otp': get_otp(self.secret),
            'next': self.next_url
        }, follow=False)
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.next_url, response.url)

    def test_without_next(self):
        """
        Test without the "next"
        """
        response = self.client.get('/hub/auth/login', follow=True)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser').find('form', attrs={
            'data-ui-relevance': 'main-login'
        }).find_next('input', attrs={
            'type': 'hidden',
            'data-ui-relevance': 'next-url-tag',
            'name': 'next'
        })
        self.assertIsNone(soup)
