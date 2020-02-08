"""
Testing the Pre-Flight Check Command
"""

from contextlib import redirect_stdout
from io import StringIO
from django.core.management import call_command, CommandError
from django.test import override_settings, SimpleTestCase, TestCase

from hub_app.management.commands import preflightcheck


class PreflightcheckCommandTest(TestCase):
    """
    Test the whole command execution at once

    Attention: If you are adding new tests, you might need to change at least the configuration overrides for the
    'test_command_output_positive' test.
    """

    @override_settings(DEBUG=True)
    def test_command_output_negative(self):
        """
        Test that the command execution raises an exception on a failed test
        """
        out = StringIO()
        self.assertRaisesMessage(
            CommandError,
            'Pre-flight Check FAILED',
            call_command, preflightcheck.Command(), stdout=out
        )

    @override_settings(  # nosec
        SECRET_KEY='AK33gas(3AKK3"&KJAhjkgdöj3öjK&NK:JAG3t!JlköegjsÖ§LEKvÖLKSIOGJ$Ö',
        DEBUG=False,
        ALLOWED_HOSTS=['127.0.0.1', '192.168.1.1', '10.0.0.1']
    )
    def test_command_output_positive(self):
        """
        Test that the command is executed successfully if everything is configured fine
        """
        out = StringIO()
        call_command(preflightcheck.Command(), stdout=out)
        output = out.getvalue().strip()
        self.assertRegex(output, r'(PASSED).{0,10}$')


class PreflightcheckChecksTest(SimpleTestCase):
    """
    Test for all checks (that do not require a database connection)

    Attention: In some tests, the stdout output is captured and thrown away. Don't expect too much in the console
    window!

    It basically tests every single test by testing the check method.
    """

    def test_secret_key_test_negative(self):
        """
        Test that the check fails if the SECRET_KEY is set to default
        """
        with redirect_stdout(StringIO()):
            self.assertFalse(preflightcheck.Command().check_django_secret())

    @override_settings(SECRET_KEY='AK33gas(3AKK3"&KJAhjkgdöj3öjK&NK:JAG3t!JlköegjsÖ§LEKvÖLKSIOGJ$Ö')  # nosec
    def test_secret_key_test_positive(self):
        """
        Test that the check is successful if the SECRET_KEY is set to something non-default
        """
        with redirect_stdout(StringIO()):
            self.assertTrue(preflightcheck.Command().check_django_secret())

    @override_settings(DEBUG=True)
    def test_debug_test_negative(self):
        """
        Test that the check fails if the DEBUG mode is still on
        """
        with redirect_stdout(StringIO()):
            self.assertFalse(preflightcheck.Command().check_debug())

    @override_settings(DEBUG=False)
    def test_debug_test_positive(self):
        """
        Test that the check is successful if the DEBUG mode is off
        """
        with redirect_stdout(StringIO()):
            self.assertTrue(preflightcheck.Command().check_debug())

    @override_settings(ALLOWED_HOSTS=[])
    def test_allowed_hosts_test_negative(self):
        """
        Test that the check fails if the ALLOWED_HOSTS config is still empty
        """
        with redirect_stdout(StringIO()):
            self.assertFalse(preflightcheck.Command().check_allowed_hosts())

    @override_settings(ALLOWED_HOSTS=['127.0.0.1'])
    def test_allowed_hosts_test_positive(self):
        """
        Test that the check is successful if the ALLOWED_HOSTS config is not empty
        """
        with redirect_stdout(StringIO()):
            self.assertTrue(preflightcheck.Command().check_allowed_hosts())
