"""
Support Forms
"""
from django.forms import Form, CharField, NumberInput
from django.utils.translation import gettext_lazy as _

from hub_app.authlib.totp.validators import OtpValidator


class TestYourAppOtpForm(Form):
    """
    Simple form for OTP validation
    """

    otp_to_be_tested = CharField(max_length=6, min_length=6, required=True,
                                 label=_('One Time Password from your app to test'),
                                 validators=[OtpValidator()], widget=NumberInput())
    otp_to_be_tested.widget.attrs.update({  # pylint: disable=no-member
        'pattern': '[0-9]{6,6}', 'class': 'form-control',
    })
