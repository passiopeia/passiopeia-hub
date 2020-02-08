from contextlib import redirect_stdout
from io import StringIO
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings

from hub_app.management.commands import preflightcheck


class PreflightcheckCommandTest(TestCase):

    @override_settings(DEBUG=True)
    def test_command_output_negative(self):
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
        out = StringIO()
        call_command(preflightcheck.Command(), stdout=out)
        output = out.getvalue().strip()
        self.assertRegex(output, r'(PASSED).{0,10}$')

    def test_secret_key_test_negative(self):
        with redirect_stdout(StringIO()):
            self.assertFalse(preflightcheck.Command().check_django_secret())

    @override_settings(SECRET_KEY='AK33gas(3AKK3"&KJAhjkgdöj3öjK&NK:JAG3t!JlköegjsÖ§LEKvÖLKSIOGJ$Ö')  # nosec
    def test_secret_key_test_positive(self):
        with redirect_stdout(StringIO()):
            self.assertTrue(preflightcheck.Command().check_django_secret())

    @override_settings(DEBUG=True)
    def test_debug_test_negative(self):
        with redirect_stdout(StringIO()):
            self.assertFalse(preflightcheck.Command().check_debug())

    @override_settings(DEBUG=False)
    def test_debug_test_positive(self):
        with redirect_stdout(StringIO()):
            self.assertTrue(preflightcheck.Command().check_debug())

    @override_settings(ALLOWED_HOSTS=[])
    def test_allowed_hosts_test_negative(self):
        with redirect_stdout(StringIO()):
            self.assertFalse(preflightcheck.Command().check_allowed_hosts())

    @override_settings(ALLOWED_HOSTS=['127.0.0.1'])
    def test_allowed_hosts_test_positive(self):
        with redirect_stdout(StringIO()):
            self.assertTrue(preflightcheck.Command().check_allowed_hosts())
