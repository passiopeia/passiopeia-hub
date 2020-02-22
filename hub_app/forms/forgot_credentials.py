"""
Forms for the Forgotten Credentials workflow
"""
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.forms import Form, ChoiceField, RadioSelect, CharField, PasswordInput, NumberInput, EmailField, HiddenInput
from django.utils.translation import gettext_lazy as _

from hub_app.authlib.forgot_credentials import RECOVERY_CHOICES
from hub_app.authlib.totp.validators import OtpValidator


class ForgottenCredentialsStep1Form(Form):
    """
    Select the kind of Restoration
    """

    step1 = ChoiceField(
        widget=RadioSelect(),
        choices=RECOVERY_CHOICES,
        required=True,
        error_messages={
            'required': _('You must select the item you have lost'),
            'invalid_choice': _('%(value)s is not a valid choice')
        }
    )


class RequestUsernameForm(Form):
    """
    You know your username?
    """

    username = CharField(min_length=3, max_length=150, required=True, validators=[ASCIIUsernameValidator()],
                         label=_('Username'))
    username.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class RequestPasswordForm(Form):
    """
    Know your password?
    """

    password = CharField(widget=PasswordInput(), required=True, max_length=1024, min_length=8, label=_('Password'))
    password.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class RequestOtpForm(Form):
    """
    Know a OTP?
    """

    otp = CharField(max_length=6, min_length=6, required=True, validators=[OtpValidator()], widget=NumberInput(),
                    label=_('One Time Password'))
    otp.widget.attrs.update({  # pylint: disable=no-member
        'pattern': '[0-9]{6,6}',
        'class': 'form-control',
    })


class ForgottenCredentialsStep2BaseForm(Form):
    """
    The basics for everything: The E-Mail address
    """

    email = EmailField(label=_('E-Mail Address'))
    email.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class ForgottenCredentialsStep2LostUsernameForm(ForgottenCredentialsStep2BaseForm, RequestPasswordForm, RequestOtpForm):
    """
    Required when the Username is lost
    """


class ForgottenCredentialsStep2LostPasswordForm(ForgottenCredentialsStep2BaseForm, RequestUsernameForm, RequestOtpForm):
    """
    Required when the Password is lost
    """


class ForgottenCredentialsStep2LostOtpForm(ForgottenCredentialsStep2BaseForm, RequestUsernameForm, RequestPasswordForm):
    """
    Required when the OTP is lost
    """


class ForgottenCredentialsStep3BaseForm(Form):
    """
    Using Auth in a Form
    """

    auth = CharField(max_length=500, min_length=250, required=True, widget=HiddenInput())


class ForgottenCredentialsStep3NewPasswordForm(ForgottenCredentialsStep3BaseForm, RequestPasswordForm):
    """
    Request a new password
    """

    password_repeat = CharField(widget=PasswordInput(), required=True, max_length=1024, min_length=8,
                                label=_('Repeat Password'))
    password_repeat.widget.attrs.update({  # pylint: disable=no-member
        'class': 'form-control',
    })


class ForgottenCredentialsStep3ConfirmOtpForm(ForgottenCredentialsStep3BaseForm, RequestOtpForm):
    """
    Request a confirmed OTP
    """
