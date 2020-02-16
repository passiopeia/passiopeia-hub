"""
Forms for Authentication
"""
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.forms import Form, CharField, NumberInput, PasswordInput

from django.utils.translation import gettext_lazy as _

from hub_app.authlib.totp.validators import OtpValidator


class UsernamePasswordOtpForm(Form):
    """
    Standard Username / Password Form
    """
    username = CharField(
        max_length=150,
        min_length=3,
        required=True,
        label=_('Username'),
        validators=[
            ASCIIUsernameValidator(),
        ]
    )
    username.widget.attrs.update({  # pylint: disable=no-member
        'aria-describedby': 'usernameHelp',
        'pattern': r'[\w.@+-]{3,150}',
        'class': 'form-control',
    })

    password = CharField(
        widget=PasswordInput(),
        required=True,
        max_length=1024,
        min_length=8,
        label=_('Password'),
    )
    password.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })

    otp = CharField(
        max_length=6,
        min_length=6,
        required=True,
        label=_('One Time Password'),
        validators=[
            OtpValidator(),
        ],
        widget=NumberInput(),
    )
    otp.widget.attrs.update({  # pylint: disable=no-member
        'aria-describedby': 'otpHelp',
        'pattern': '[0-9]{6,6}',
        'class': 'form-control',
    })
