"""
Forgotten Credentials workflow
"""
from base64 import b64encode, b64decode
from random import SystemRandom
from time import sleep
from urllib.parse import quote
from uuid import UUID

from csp.decorators import csp_update
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.signing import Signer, BadSignature
from django.db import transaction, DatabaseError
from django.http import HttpRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.totp.token import get_possible_otps, create_random_totp_secret
from hub_app.forms.forgot_credentials import ForgottenCredentialsStep1Form, \
    ForgottenCredentialsStep2LostPasswordForm, ForgottenCredentialsStep2LostUsernameForm, \
    ForgottenCredentialsStep2LostOtpForm, ForgottenCredentialsStep3BaseForm, ForgottenCredentialsStep3NewPasswordForm, \
    ForgottenCredentialsStep3ConfirmOtpForm
from hub_app.models import HubUser, PendingCredentialRecovery


class ForgotCredentialsFirstStepView(View):
    """
    The Password Reset procedure
    """

    content_type = 'text/html'
    template_name = 'hub_app/auth/forgot-credentials/step1.html'
    http_method_names = ['get', 'post']

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            return redirect(reverse_lazy('ha:auth:fc:step.1'), permanent=False)
        return super(ForgotCredentialsFirstStepView, self).dispatch(request, *args, **kwargs)

    def send_form(self, request, form: ForgottenCredentialsStep1Form = ForgottenCredentialsStep1Form()):
        """
        Deliver the form
        """
        return render(request, self.template_name, {
            'form': form,
        }, content_type=self.content_type)

    def get(self, request: HttpRequest):
        """
        Handle the GET request
        """
        return self.send_form(request)

    def post(self, request: HttpRequest):
        """
        Handle the POST request
        """
        form = ForgottenCredentialsStep1Form(request.POST)
        if not form.is_valid():
            return self.send_form(request, form)
        lost = form.cleaned_data['step1']
        request.session['forgotten_credentials_type'] = lost
        return redirect(reverse_lazy('ha:auth:fc:step.2', kwargs={'lost': lost}), permanent=False)


class ForgotCredentialsSecondStepView(View):
    """
    Get the data the user still knows
    """

    content_type = 'text/html'
    template_name = 'hub_app/auth/forgot-credentials/step2.html'
    http_method_names = ['get', 'post']

    form_types = {
        'password': ForgottenCredentialsStep2LostPasswordForm,
        'username': ForgottenCredentialsStep2LostUsernameForm,
        'otp-secret': ForgottenCredentialsStep2LostOtpForm,
    }

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if request.session.get('forgotten_credentials_type', None) is None:  # pragma: no cover  # Session safeguard
            return HttpResponseForbidden()
        return super(ForgotCredentialsSecondStepView, self).dispatch(request, *args, **kwargs)

    def _send_form(self, request: HttpRequest, form):
        """
        Deliver the form
        """
        return render(request, self.template_name, {
            'form': form,
            'lost': request.session['forgotten_credentials_type'],
        }, content_type=self.content_type)

    def get(self, request: HttpRequest, lost: str):
        """
        Handle the GET request
        """
        return self._send_form(request, self.form_types.get(lost))

    def report(self, request: HttpRequest, multiple: bool = False):
        """
        Report success, but sleep randomly before, to mitigate timing attacks
        """
        logout(request)
        random = SystemRandom()
        sleep(random.randint(50, 750) / 1000)  # nosec  # No cryptographic use
        template = 'hub_app/auth/forgot-credentials/step2-success.html'
        if multiple:
            template = 'hub_app/auth/forgot-credentials/step2-multiple-objects.html'
        return render(request, template, content_type=self.content_type)

    @staticmethod
    def verify_password(user: HubUser, password: str):
        """
        Verify that the password matches the user
        """
        return user.check_password(password)

    @staticmethod
    def verify_otp(user: HubUser, otp: str):
        """
        Verify that the OTP matches the user
        """
        return otp in get_possible_otps(user.get_totp_secret())

    @staticmethod
    def verify_username(user: HubUser, username: str):
        """
        Verify that the username matches the user
        """
        return username.lower() == user.username.lower()

    def create_recovery(self, request: HttpRequest, user: HubUser, lost: str):
        """
        Create a Recovery
        """
        with transaction.atomic():
            tx_id = transaction.savepoint()
            try:
                recovery = PendingCredentialRecovery.objects.create(
                    user=user,
                    recovery_type=lost
                )  # type: PendingCredentialRecovery
            except DatabaseError:  # pragma: no cover  # Safeguard for database problems
                transaction.savepoint_rollback(tx_id)
                return self.report(request)
            recovery_uuid = str(recovery.uuid)
            recovery_key = recovery.key
            signed_recovery_key = Signer(salt=recovery_uuid).sign(recovery_key)
            protocol = 'http'
            if request.is_secure():  # pragma: no cover  # Test requests are always not secure
                protocol += 's'
            recovery_link = '{}://{}{}?auth={}'.format(
                protocol, request.get_host(), reverse('ha:auth:fc:step.3', kwargs={'recovery': recovery_uuid}),
                quote(signed_recovery_key)
            )
            try:
                recovery_mail = EmailMessage(
                    to=[user.email],
                    from_email=settings.EMAIL_RECOVERY_FROM,
                    subject=settings.EMAIL_RECOVERY_SUBJECT,
                    body=get_template('hub_app/auth/forgot-credentials/recovery-email.txt').render({
                        'recovery_url': recovery_link,
                        'first_name': user.first_name,
                    })
                )
                recovery_mail.send(fail_silently=False)
            except (OSError, ValueError):  # pragma: no cover  # Safeguard for mail sending errors and template errors
                transaction.savepoint_rollback(tx_id)
                return self.report(request)
            transaction.savepoint_commit(tx_id)
        return self.report(request)

    def handle_lost_username(self,
                             request: HttpRequest, user: HubUser, form: ForgottenCredentialsStep2LostUsernameForm):
        """
        Handle Lost Username
        """
        if not ForgotCredentialsSecondStepView.verify_password(user, form.cleaned_data['password']) \
                or not ForgotCredentialsSecondStepView.verify_otp(user, form.cleaned_data['otp']):
            return self.report(request)
        return self.create_recovery(request, user, 'username')

    def handle_lost_password(self,
                             request: HttpRequest, user: HubUser, form: ForgottenCredentialsStep2LostPasswordForm):
        """
        Handle Lost Password
        """
        if not ForgotCredentialsSecondStepView.verify_username(user, form.cleaned_data['username']) \
                or not ForgotCredentialsSecondStepView.verify_otp(user, form.cleaned_data['otp']):
            return self.report(request)
        return self.create_recovery(request, user, 'password')

    def handle_lost_otp_secret(self,
                               request: HttpRequest, user: HubUser, form: ForgottenCredentialsStep2LostOtpForm):
        """
        Handle Lost OTP Secret
        """
        if not ForgotCredentialsSecondStepView.verify_password(user, form.cleaned_data['password']) \
                or not ForgotCredentialsSecondStepView.verify_username(user, form.cleaned_data['username']):
            return self.report(request)
        return self.create_recovery(request, user, 'otp-secret')

    def post(self, request: HttpRequest, lost: str):
        """
        Handle POST request
        """
        form = self.form_types.get(lost)(request.POST)
        if not form.is_valid():
            return self._send_form(request, form)
        handler_methods = {
            'password': self.handle_lost_password,
            'username': self.handle_lost_username,
            'otp-secret': self.handle_lost_otp_secret,
        }
        try:
            user = HubUser.objects.filter(
                is_active=True, pendingregistration__isnull=True, pendingcredentialrecovery__isnull=True
            ).get(
                email__iexact=form.cleaned_data['email'].strip().lower()
            )
        except HubUser.DoesNotExist:
            return self.report(request)
        except HubUser.MultipleObjectsReturned:
            return self.report(request, True)
        return handler_methods[lost](request, user, form)


class ForgotCredentialsThirdStepView(View):
    """
    Create new Credentials
    """

    content_type = 'text/html'

    def report(self, request: HttpRequest, what: str, context: dict = None):
        """
        Send a response to the user
        """
        return render(request, 'hub_app/auth/forgot-credentials/step3-{}.html'.format(what), context=context,
                      content_type=self.content_type)

    def request_password(self, request: HttpRequest, auth: str, recovery: str):
        """
        Request a new Password from the user
        """
        return self.report(request, 'request-password', {
            'recovery': recovery,
            'form': ForgottenCredentialsStep3NewPasswordForm(initial={
                'auth': auth
            })
        })

    def reveal_information(self, request: HttpRequest, auth: str, recovery: str, what: str):
        """
        Reveal information
        """
        return self.report(request, 'reveal-{}'.format(what), {
            'recovery': recovery,
            'form': ForgottenCredentialsStep3BaseForm(initial={
                'auth': auth
            })
        })

    def get(self, request: HttpRequest, recovery: UUID):
        """
        Handle the get request - comes from an E-Mail
        """
        url_form = ForgottenCredentialsStep3BaseForm(request.GET)
        if not url_form.is_valid():
            return self.report(request, 'invalid-link')
        signer = Signer(salt=str(recovery))
        try:
            auth = signer.unsign(url_form.cleaned_data['auth'])
        except (BadSignature, ValueError):
            return self.report(request, 'invalid-link')
        try:
            pending_recovery = PendingCredentialRecovery.objects.filter(
                user__is_active=True, valid_until__gte=now()
            ).get(uuid=recovery)  # type: PendingCredentialRecovery
        except PendingCredentialRecovery.DoesNotExist:
            return self.report(request, 'invalid-link')
        if pending_recovery.key != auth:  # pragma: no cover  # Safeguard, can only happen with compromised security key
            return self.report(request, 'invalid-link')
        if pending_recovery.recovery_type == 'password':
            return self.request_password(request, url_form.cleaned_data['auth'], str(recovery))
        return self.reveal_information(
            request, url_form.cleaned_data['auth'], str(recovery), pending_recovery.recovery_type
        )


class ForgotCredentialsSetNewPasswordView(View):
    """
    Set a new password
    """

    http_method_names = ['post']

    content_type = 'text/html'
    template_name = 'hub_app/auth/forgot-credentials/step3-request-password.html'

    def send_form(self, request: HttpRequest, form: ForgottenCredentialsStep3NewPasswordForm, recovery: str):
        """
        Send the form back to the user
        """
        return render(request, self.template_name, {
            'form': form,
            'recovery': recovery
        }, content_type=self.content_type)

    def post(self, request: HttpRequest, recovery: UUID):
        """
        Handle the POST request
        """
        recovery_str = str(recovery)
        form = ForgottenCredentialsStep3NewPasswordForm(request.POST)
        if not form.is_valid():
            return self.send_form(request, form, recovery_str)
        if form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
            form.add_error(None, _("The two passwords don't match"))
            return self.send_form(request, form, recovery_str)
        signer = Signer(salt=recovery_str)
        try:
            auth = signer.unsign(form.cleaned_data['auth'])
        except (BadSignature, ValueError):  # pragma: no cover  # Manipulation Safeguard
            form.add_error(None, _('The Authentication Signature is invalid.') + ' ' +
                           _('Please contact our support team. Error Code: %(code)s') % {'code': 'EA01'})
            return self.send_form(request, form, recovery_str)
        try:
            recovery_data = PendingCredentialRecovery.objects.filter(
                user__is_active=True, valid_until__gte=now(), recovery_type='password'
            ).get(uuid=recovery, key=auth)  # type: PendingCredentialRecovery
        except PendingCredentialRecovery.DoesNotExist:  # pragma: no cover  # Database Safeguard
            form.add_error(None, _('The request for Credential Recovery is invalid.') + ' ' +
                           _('Please contact our support team. Error Code: %(code)s') % {'code': 'EA02'})
            return self.send_form(request, form, recovery_str)
        user = recovery_data.user
        try:
            validate_password(form.cleaned_data['password'], user=user)
        except ValidationError as validation_error:
            form.add_error(None, validation_error.messages)
            return self.send_form(request, form, recovery_str)
        with transaction.atomic():
            tx_id = transaction.savepoint()
            user.set_password(form.cleaned_data['password'])
            user.save()
            recovery_data.delete()
            transaction.savepoint_commit(tx_id)
        logout(request)
        messages.add_message(request, messages.SUCCESS, _('Your password has been updated. You can login now.'))
        return redirect(reverse_lazy('ha:auth:login'))


def deny_step(request: HttpRequest, error_code: str):
    """
    Deny the step
    """
    logout(request)
    messages.add_message(request, messages.ERROR, _('Unable to verify your request.') + ' ' +
                         _('Please contact our support team. Error Code: %(code)s') % {'code': error_code})
    return redirect(reverse_lazy('ha:home'))


class ForgotCredentialsRevealNewOtpSecret(View):
    """
    Reveal a new OtpSecret
    """

    http_method_names = ['post']

    content_type = 'text/html'
    template_name = 'hub_app/auth/forgot-credentials/step3-show-new-secret.html'

    @csp_update(IMG_SRC='data:')
    def dispatch(self, request, *args, **kwargs):
        return super(ForgotCredentialsRevealNewOtpSecret, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, recovery: UUID):
        """
        Set new temporary Secret and display it, ask the user to confirm with an OTP
        """
        form = ForgottenCredentialsStep3BaseForm(request.POST)
        if not form.is_valid():
            return deny_step(request, 'EA04')
        recovery_str = str(recovery)
        try:
            auth = Signer(salt=recovery_str).unsign(form.cleaned_data['auth'])
            user = PendingCredentialRecovery.objects.filter(
                user__is_active=True, valid_until__gte=now(), recovery_type='otp-secret'
            ).get(uuid=recovery, key=auth).user
        except PendingCredentialRecovery.DoesNotExist:  # pragma: no cover  # Database Safeguard
            return deny_step(request, 'EA05')
        except (ValueError, BadSignature):  # pragma: no cover  # Manipulation Safeguard
            return deny_step(request, 'EA06')
        new_secret = create_random_totp_secret()
        new_secret_encrypted = b64encode(SymmetricCrypt().encrypt(new_secret)).decode('us-ascii')
        request.session['encrypted_temporary_otp_secret'] = new_secret_encrypted
        return render(request, self.template_name, {
            'new_secret': new_secret,
            'username': user.username,
            'recovery': recovery_str,
            'form': ForgottenCredentialsStep3ConfirmOtpForm(initial={
                'auth': form.cleaned_data['auth']
            })
        }, content_type=self.content_type)


class ForgotCredentialsConfirmNewOtpSecret(View):
    """
    Confirm a new OtpSecret
    """

    http_method_names = ['post']

    content_type = 'text/html'
    template_name = 'hub_app/auth/forgot-credentials/step3-show-new-secret.html'

    def show_form(self, request: HttpRequest, new_secret: bytes, username: str, recovery: str,
                  form: ForgottenCredentialsStep3ConfirmOtpForm):
        """
        Show the new form
        """
        return render(request, self.template_name, {
            'new_secret': new_secret,
            'username': username,
            'recovery': recovery,
            'form': form
        }, content_type=self.content_type)

    @csp_update(IMG_SRC='data:')
    def dispatch(self, request, *args, **kwargs):
        return super(ForgotCredentialsConfirmNewOtpSecret, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, recovery: UUID):
        """
        Set the new secret
        """
        encrypted_secret = request.session.get('encrypted_temporary_otp_secret', None)
        if encrypted_secret is None:  # pragma: no cover  # Safeguard for tinkered session
            return deny_step(request, 'EA10')
        auth_form = ForgottenCredentialsStep3BaseForm(request.POST)
        if not auth_form.is_valid():  # pragma: no cover  # Safeguard Client Manipulation
            return deny_step(request, 'EA11')
        new_secret = SymmetricCrypt().decrypt(b64decode(encrypted_secret))
        recovery_str = str(recovery)
        try:
            auth = Signer(salt=recovery_str).unsign(auth_form.cleaned_data['auth'])
            recovery_data = PendingCredentialRecovery.objects.filter(
                user__is_active=True, valid_until__gte=now(), recovery_type='otp-secret'
            ).get(uuid=recovery, key=auth)
            user = recovery_data.user
        except PendingCredentialRecovery.DoesNotExist:  # pragma: no cover  # Database Safeguard
            return deny_step(request, 'EA12')
        except (ValueError, BadSignature):  # pragma: no cover  # Manipulation Safeguard
            return deny_step(request, 'EA13')
        form = ForgottenCredentialsStep3ConfirmOtpForm(request.POST)
        if not form.is_valid():
            return self.show_form(request, new_secret, user.username, recovery_str, form)
        if form.cleaned_data['otp'] not in get_possible_otps(new_secret):
            form.add_error('otp', _('This one time password is not valid.'))
            return self.show_form(request, new_secret, user.username, recovery_str, form)
        with transaction.atomic():
            tx_id = transaction.savepoint()
            user.set_totp_secret(new_secret)
            user.save()
            recovery_data.delete()
            transaction.savepoint_commit(tx_id)
        logout(request)
        messages.add_message(request, messages.SUCCESS, _('Your new OTP secret has been set. You can login now.'))
        return redirect(reverse_lazy('ha:auth:login'))


class ForgotCredentialsRevealUsername(View):
    """
    Reveal the username
    """

    http_method_names = ['post']

    content_type = 'text/html'
    template_name = 'hub_app/auth/forgot-credentials/step3-show-username.html'

    def post(self, request: HttpRequest, recovery: UUID):
        """
        Reveal the username now
        """
        auth_form = ForgottenCredentialsStep3BaseForm(request.POST)
        if not auth_form.is_valid():  # pragma: no cover  # Safeguard for Client Manipulation
            return deny_step(request, 'EA20')
        recovery_str = str(recovery)
        try:
            auth = Signer(salt=recovery_str).unsign(auth_form.cleaned_data['auth'])
            recovery_obj = PendingCredentialRecovery.objects.filter(
                user__is_active=True, valid_until__gte=now(), recovery_type='username'
            ).get(uuid=recovery, key=auth)
        except PendingCredentialRecovery.DoesNotExist:  # pragma: no cover  # Safeguard
            return deny_step(request, 'EA21')
        except (ValueError, BadSignature):  # pragma: no cover  # Safeguard
            return deny_step(request, 'EA22')
        username = str(recovery_obj.user.username)
        recovery_obj.delete()
        return render(request, self.template_name, {
            'username': username,
        }, content_type=self.content_type)
