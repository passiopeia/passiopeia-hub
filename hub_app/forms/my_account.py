"""
Forms required for the "My Account" functions
"""
from django.contrib.auth.password_validation import validate_password
from django.forms import Form, PasswordInput, CharField, NumberInput, EmailField, HiddenInput
from django.utils.translation import gettext_lazy as _

from hub_app.authlib.totp.validators import OtpValidator


class PasswordChangeForm(Form):
    """
    Password Change Form
    """

    old_password = CharField(widget=PasswordInput(), required=True, max_length=1024, label=_('Current Password'))
    old_password.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })

    new_password1 = CharField(widget=PasswordInput(), required=True, max_length=1024, min_length=8,
                              label=_('New Password'), validators=[validate_password])
    new_password1.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })

    new_password2 = CharField(widget=PasswordInput(), required=True, max_length=1024, min_length=8,
                              label=_('Repeat New Password'))
    new_password2.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class NewOtpSecretForm(Form):
    """
    Querying for a new OTP
    """

    otp_confirm = CharField(max_length=6, min_length=6, required=True, label=_('One Time Password for Confirmation'),
                            validators=[OtpValidator()], widget=NumberInput())
    otp_confirm.widget.attrs.update({  # pylint: disable=no-member
        'pattern': '[0-9]{6,6}',
        'class': 'form-control',
    })


class SetNameInformationForm(Form):
    """
    Fetching new Name Information
    """

    last_name = CharField(max_length=150, required=False, empty_value='', label=_('Last Name'))
    last_name.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })

    first_name = CharField(min_length=1, max_length=30, required=True, empty_value='', label=_('First Name'))
    first_name.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class SetEMailForm(Form):
    """
    Set a new E-Mail Address
    """

    new_email = EmailField(label=_('New E-Mail Address'))
    new_email.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class SetEMailKeyForm(Form):
    """
    Get the Key for an E-Mail change
    """

    change_key = CharField(max_length=500, min_length=250, required=True, widget=HiddenInput())
