"""
Support Views
"""
from base64 import b32decode
from typing import Optional, List

from django.http import HttpRequest
from django.shortcuts import render
from django.utils.timezone import now
from django.views import View

from hub_app.authlib.totp.token import get_possible_otps
from hub_app.forms.support import TestYourAppOtpForm


class TestYourAppView(View):
    """
    View for testing your OTP app
    """

    secret = b32decode('SXVRM2UTCEOB74ELEXRSNKZ7ATVAMLYEJ7KUTXF2OR5NZBKJWYKZPLWZIPMB'
                       'Y3ANBBKNXMPCB2S5364O4PG5JKXYWC4DIWDAKHLYHBRFLTBEQAJNHLIA====')

    content_type = 'text/html'
    template_name = 'hub_app/pages/support/test-your-app.html'

    http_method_names = ['get', 'post']

    def _send_template(self, request: HttpRequest, form: TestYourAppOtpForm = TestYourAppOtpForm(), show: bool = False,
                       chosen_otp: Optional[str] = None, list_of_otps: Optional[List[str]] = None,
                       success: bool = False):
        """
        Send the template with form to the user
        """
        return render(request, self.template_name, {
            'form': form,
            'list_of_otps': list_of_otps,
            'chosen_otp': chosen_otp,
            'success': success,
            'show': show,
            'now': now(),
        }, content_type=self.content_type)

    def get(self, request: HttpRequest):
        """
        Just deliver the template
        """
        return self._send_template(request)

    def post(self, request: HttpRequest):
        """
        Check the Code
        """
        form = TestYourAppOtpForm(request.POST)
        if not form.is_valid():
            return self._send_template(request, form)
        chosen_otp = form.cleaned_data['otp_to_be_tested']
        success = chosen_otp in get_possible_otps(self.secret)
        list_of_otps = get_possible_otps(self.secret, -10, 10)
        return self._send_template(request, form, True, chosen_otp, list_of_otps, success)
