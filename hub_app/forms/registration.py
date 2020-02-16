"""
Forms for the registration
"""
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.forms import Form, CharField, EmailField, UUIDField, HiddenInput, PasswordInput, NumberInput

from django.utils.translation import gettext_lazy as _

from hub_app.authlib.totp.validators import OtpValidator
from hub_app.reglib.validators import validate_unique_username


class RegistrationStep1Form(Form):
    """
    Form for Step 1
    """

    username = CharField(min_length=3, max_length=150, required=True, validators=[
        ASCIIUsernameValidator(),
        validate_unique_username
    ], label=_('Username'))
    username.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
        'aria-describedby': 'usernameHelp'
    })

    email = EmailField(label=_('E-Mail Address'))
    email.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
        'aria-describedby': 'emailHelp'
    })

    first_name = CharField(max_length=30, min_length=1, required=True, empty_value=None, label=_('First Name'))
    first_name.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })

    last_name = CharField(max_length=150, required=False, empty_value=None, label=_('Last Name'))
    last_name.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class RegistrationStep2UrlForm(Form):
    """
    Only required for URL validation
    """

    reg = UUIDField(required=True, widget=HiddenInput())
    key = CharField(max_length=500, min_length=250, required=True, widget=HiddenInput())


class RegistrationStep2Form(RegistrationStep2UrlForm):
    """
    Get password and otp from user
    """

    password1 = CharField(widget=PasswordInput(), required=True, max_length=1024, min_length=8, label=_('Password'),
                          validators=[validate_password])
    password1.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })

    password2 = CharField(widget=PasswordInput(), required=True, max_length=1024, min_length=8,
                          label=_('Repeat Password'))
    password2.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })

    otp = CharField(max_length=6, min_length=6, required=True, label=_('One Time Password from your app'),
                    validators=[OtpValidator()], widget=NumberInput())
    otp.widget.attrs.update({  # pylint: disable=no-member
        'pattern': '[0-9]{6,6}',
        'class': 'form-control',
    })
