"""
Views for MyAccount
"""
from base64 import b64decode, b64encode
from urllib.parse import quote
from uuid import UUID

from csp.decorators import csp_update
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.signing import Signer, BadSignature
from django.db import DatabaseError, transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.totp.token import create_encrypted_random_totp_secret, get_possible_otps
from hub_app.forms.my_account import PasswordChangeForm, NewOtpSecretForm, SetNameInformationForm, SetEMailForm, \
    SetEMailKeyForm
from hub_app.models import HubUser, PendingEMailChange


class MyAccountOverviewView(LoginRequiredMixin, TemplateView):
    """
    Show User's Account Start page
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/overview.html'


class MyAccountCredentialsOverviewView(LoginRequiredMixin, TemplateView):
    """
    Overview over Credential Options
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/credentials-overview.html'


class MyAccountCredentialsPasswordView(LoginRequiredMixin, View):
    """
    Change Password

    Credentials > Password
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/credentials-password.html'

    http_method_names = ['get', 'post']

    def _send_password_change_form(self, request: HttpRequest, form: PasswordChangeForm = PasswordChangeForm()):
        """
        Send the form back to the user
        """
        return render(request, self.template_name, {'form': form}, content_type=self.content_type)

    def get(self, request: HttpRequest):
        """
        Only show Form and Stuff
        """
        return self._send_password_change_form(request)

    def post(self, request: HttpRequest):
        """
        Handle the Change
        """
        form = PasswordChangeForm(request.POST)
        if not form.is_valid():
            return self._send_password_change_form(request, form)
        additional_errors = False
        if form.cleaned_data['new_password1'] != form.cleaned_data['new_password2']:
            form.add_error('new_password2', _('The passwords do not match'))
            additional_errors = True
        try:
            validate_password(form.cleaned_data['new_password1'], user=request.user)
        except ValidationError as validation_error:
            form.add_error('new_password1', validation_error)
            additional_errors = True
        if additional_errors:
            return self._send_password_change_form(request, form)
        if not request.user.check_password(form.cleaned_data['old_password']):
            form.add_error('old_password', _('This is not your current password'))
            return self._send_password_change_form(request, form)
        try:
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
        except DatabaseError as db_error:  # pragma: no cover  # Database Safeguard
            form.add_error(None, _('Unable to save the password: %(error)s') % {'error': db_error})
            return self._send_password_change_form(request, form)
        logout(request)
        messages.add_message(request, messages.SUCCESS, _('New Password set successfully. You can re-login now.'))
        return redirect(
            '{}?next={}'.format(
                reverse('ha:auth:login'),
                quote(reverse('ha:acc:credentials.password'))
            ),
            permanent=False
        )


class MyAccountCredentialsOtpSecretView(LoginRequiredMixin, View):
    """
    Change OTP Secret

    Credentials > OTP
    """
    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/credentials-otp-secret.html'

    http_method_names = ['get', 'post', 'put']

    put_okay_response = {'secret_created': True}
    put_fail_response = {'secret_created': False}

    @csp_update(IMG_SRC='data:')
    def dispatch(self, request, *args, **kwargs):
        return super(MyAccountCredentialsOtpSecretView, self).dispatch(request, *args, **kwargs)

    def _send_otp_form(self, request: HttpRequest, form: NewOtpSecretForm = NewOtpSecretForm(), success: bool = False):
        """
        Send the OTP form
        """
        secret = request.session.get('encrypted_new_totp_secret', None)
        if secret is not None:
            secret = SymmetricCrypt().decrypt(b64decode(secret.encode('us-ascii')))
        return render(request, self.template_name, {
            'form': form,
            'new_secret': secret,
            'username': request.user.username,
            'success': success,
        }, content_type=self.content_type)

    def get(self, request: HttpRequest):
        """
        Only the form
        """
        return self._send_otp_form(request)

    def put(self, request: HttpRequest):
        """
        Set the secret, tell ok
        """
        if request.session.get('encrypted_new_totp_secret', None) is None:
            new_secret = create_encrypted_random_totp_secret()
            request.session['encrypted_new_totp_secret'] = b64encode(new_secret).decode('us-ascii')
            return JsonResponse(self.put_okay_response)
        return JsonResponse(self.put_fail_response)

    def post(self, request: HttpRequest):
        """
        Set the new secret
        """
        form = NewOtpSecretForm(request.POST)
        if not form.is_valid():
            return self._send_otp_form(request, form)
        secret = request.session.get('encrypted_new_totp_secret', None)
        if secret is None:
            form.add_error(None, _('No Secret set. Please create a new secret first.'))
            return self._send_otp_form(request, form)
        secret = SymmetricCrypt().decrypt(b64decode(secret.encode('us-ascii')))
        if form.cleaned_data['otp_confirm'] not in get_possible_otps(secret):
            form.add_error('otp_confirm', _('One-time password invalid'))
            return self._send_otp_form(request, form)
        del request.session['encrypted_new_totp_secret']
        try:
            user = HubUser.objects.get(id=request.user.id)
            user.set_totp_secret(secret)
            user.save()
        except DatabaseError:  # pragma: no cover  # Database Safeguard
            form.add_error(None, _('We are currently unable to update your OTP Secret. Please try again later.'))
            return self._send_otp_form(request, form)
        return self._send_otp_form(request, success=True)


class MyAccountDatabasesOverviewView(LoginRequiredMixin, TemplateView):
    """
    Overview over Database Options
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/databases.html'


class MyAccountPersonalOverviewView(LoginRequiredMixin, TemplateView):
    """
    Overview over Personal Options
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/personal-overview.html'


class MyAccountPersonalNameView(LoginRequiredMixin, View):
    """
    Personal Options > Name
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/personal-name.html'

    http_method_names = ['get', 'post']

    def _send_user_info_form(self, request: HttpRequest, form: SetNameInformationForm = None, success: bool = False):
        """
        Send the Form
        """
        if form is None:
            form = SetNameInformationForm(initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            })
        return render(request, self.template_name, {
            'form': form,
            'success': success,
        }, content_type=self.content_type)

    def get(self, request: HttpRequest):
        """
        Just send the form
        """
        return self._send_user_info_form(request)

    def post(self, request: HttpRequest):
        """
        Save the new data
        """
        form = SetNameInformationForm(request.POST)
        if not form.is_valid():
            return self._send_user_info_form(request, form)
        try:
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
        except DatabaseError:  # pragma: no cover  # Database Safeguard
            form.add_error(None, _('We are currently unable to save your information. Please try again later.'))
            return self._send_user_info_form(request, form)
        return self._send_user_info_form(request, form, True)


class MyAccountPersonalEMailView(LoginRequiredMixin, View):
    """
    Personal Options > E-Mail
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/personal-email.html'

    http_method_names = ['get', 'post']

    @staticmethod
    def _test_can_change(request: HttpRequest):
        """
        Test if a user can change ones E-Mail Address
        """
        try:
            PendingEMailChange.objects.get(user=request.user)
            return False
        except PendingEMailChange.DoesNotExist:
            return True

    def _send_email_form(self, request: HttpRequest, form: SetEMailForm = None, success: bool = False,
                         not_allowed: bool = False):
        """
        Send the E-Mail Form to the client
        """
        if form is None:
            form = SetEMailForm(initial={
                'new_email': request.user.email
            })
        return render(request, self.template_name, {
            'form': form,
            'success': success,
            'not_allowed': not_allowed,
        }, content_type=self.content_type)

    def get(self, request: HttpRequest):
        """
        Handle the GET request
        """
        return self._send_email_form(request, not_allowed=not MyAccountPersonalEMailView._test_can_change(request))

    def post(self, request: HttpRequest):
        """
        Handle the POST request
        """
        if not MyAccountPersonalEMailView._test_can_change(request):
            return self._send_email_form(request, not_allowed=True)
        form = SetEMailForm(request.POST)
        if not form.is_valid():
            return self._send_email_form(request, form)
        email = form.cleaned_data['new_email'].strip().lower()
        with transaction.atomic():
            tx_id = transaction.savepoint()
            try:
                change = PendingEMailChange.objects.create(user=request.user, new_email=email)
                change_uuid = str(change.uuid)
                change_key = change.key
                key_signer = Signer(salt=change_uuid)
                signed_change_code = key_signer.sign(change_key)
                protocol = 'http'
                if request.is_secure():  # pragma: no cover  # Test requests are always not secure
                    protocol += 's'
                url = '{}://{}{}?change_key={}'.format(
                    protocol,
                    request.get_host(),
                    reverse('ha:acc:personal.email.verify', kwargs={
                        'change': change_uuid
                    }),
                    quote(signed_change_code)
                )
                verification_mail = EmailMessage(
                    to=[email],
                    from_email=settings.EMAIL_VERIFICATION_FROM,
                    subject=settings.EMAIL_VERIFICATION_SUBJECT,
                    body=get_template('hub_app/my-account/change-email.txt').render({
                        'change_url': url,
                        'first_name': request.user.first_name,
                    })
                )
                verification_mail.send(fail_silently=False)
                transaction.savepoint_commit(tx_id)
                return self._send_email_form(request, success=True)
            except (DatabaseError, OSError, ValueError):  # pragma: no cover  # Database Safeguard
                transaction.savepoint_rollback(tx_id)
                form.add_error(None,
                               _("We're experiencing problems creating your change request. Please try again later."))
                return self._send_email_form(request, form)


class MyAccountPersonalEMailVerifyView(LoginRequiredMixin, View):
    """
    Verify new E-Mail address
    """

    raise_exception = False
    content_type = 'text/html'
    template_name = 'hub_app/my-account/personal-email-confirm.html'

    http_method_names = ['get', 'post']

    def _send_confirmation_form(self, request: HttpRequest, uuid: UUID, form: SetEMailKeyForm, link_error: bool = False,
                                success: bool = False, new_email: str = None):
        """
        Send responses
        """
        return render(request, self.template_name, {
            'form': form,
            'uuid': uuid,
            'success': success,
            'link_error': link_error,
            'new_email': new_email,
        }, content_type=self.content_type)

    def get(self, request: HttpRequest, change: UUID):
        """
        Handle the GET - Coming from an E-Mail
        """
        form = SetEMailKeyForm(request.GET)
        if not form.is_valid():
            return self._send_confirmation_form(request, change, form, link_error=True)
        try:
            change_request = PendingEMailChange.objects.filter(
                user=request.user, valid_until__gte=now()
            ).get(uuid=change)
        except PendingEMailChange.DoesNotExist:
            return self._send_confirmation_form(request, change, form, link_error=True)
        try:
            key = Signer(salt=str(change)).unsign(form.cleaned_data['change_key'])
        except (BadSignature, ValueError):
            return self._send_confirmation_form(request, change, form, link_error=True)
        if key != change_request.key:  # pragma: no cover  # Can only happen when the security key is compromised
            return self._send_confirmation_form(request, change, form, link_error=True)
        return self._send_confirmation_form(request, change, form, new_email=change_request.new_email)

    def post(self, request: HttpRequest, change: UUID):
        """
        Do the change
        """
        form = SetEMailKeyForm(request.POST)
        if not form.is_valid():
            return self._send_confirmation_form(request, change, form)
        try:
            change_request = PendingEMailChange.objects.filter(
                user=request.user, valid_until__gte=now()
            ).get(uuid=change)
        except PendingEMailChange.DoesNotExist:
            form.add_error(None, _("There is no E-Mail change waiting to be completed. Maybe it's already expired."))
            return self._send_confirmation_form(request, change, form)
        email = change_request.new_email
        try:
            key = Signer(salt=str(change)).unsign(form.cleaned_data['change_key'])
        except (BadSignature, ValueError):
            form.add_error('change_key', _("Your Change Key's signature gone invalid."))
            return self._send_confirmation_form(request, change, form, new_email=email)
        if key != change_request.key:
            form.add_error('change_key', _('Your Change Key does not match our records.'))
            return self._send_confirmation_form(request, change, form, new_email=email)
        with transaction.atomic():
            tx_id = transaction.savepoint()
            try:
                new_mail = change_request.new_email
                request.user.email = new_mail
                request.user.save()
                change_request.delete()
                transaction.savepoint_commit(tx_id)
            except DatabaseError:  # pragma: no cover  # Database Safeguard
                transaction.savepoint_rollback(tx_id)
                form.add_error(None, _('Currently we are not able to setup your new E-Mail address. '
                                       'Please try again later.'))
                return self._send_confirmation_form(request, change, form, new_email=email)
        return self._send_confirmation_form(request, change, form, success=True)
