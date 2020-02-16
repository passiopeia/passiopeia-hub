"""
Views for registration
"""
from base64 import b64encode, b64decode
from urllib.parse import quote

from csp.decorators import csp_update
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.signing import Signer, BadSignature
from django.db import transaction, DatabaseError
from django.http import HttpRequest
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View

from hub_app.authlib.totp.token import get_possible_otps
from hub_app.forms.registration import RegistrationStep1Form, RegistrationStep2UrlForm, RegistrationStep2Form
from hub_app.models import HubUser, PendingRegistration


class RegistrationFirstStepView(UserPassesTestMixin, View):
    """
    First step of the registration
    """

    http_method_names = ['get', 'post']

    template_name = 'hub_app/registration/step1.html'
    success_template_name = 'hub_app/registration/step1-success.html'
    content_type = 'text/html'

    raise_exception = True

    def test_func(self):
        return self.request.user.is_anonymous

    def _send_form(self, request, form: RegistrationStep1Form = RegistrationStep1Form()):
        """
        Send the form to the user
        """
        return render(request, self.template_name, {
            'form': form
        }, content_type=self.content_type)

    def get(self, request: HttpRequest):
        """
        Handle the get request
        """
        return self._send_form(request)

    def post(self, request: HttpRequest):
        """
        Handle the post request
        """
        form = RegistrationStep1Form(request.POST)
        if not form.is_valid():
            return self._send_form(request, form)
        with transaction.atomic():
            tx_id = transaction.savepoint()
            email = form.cleaned_data['email'].strip().lower()
            first_name = form.cleaned_data['first_name'].strip()
            try:
                new_user = HubUser.objects.create_user(
                    username=form.cleaned_data['username'].strip().lower(),
                    email=email,
                    first_name=first_name,
                    is_active=True
                )  # type: HubUser
                new_user.set_unusable_password()
                new_user.save()
                registration = PendingRegistration.objects.create(
                    user=new_user
                )  # type: PendingRegistration
            except DatabaseError:
                transaction.savepoint_rollback(tx_id)
                form.add_error(
                    None,
                    _('Something went wrong and the registration step could not be finished. Please try again later.')
                )
                return self._send_form(request, form)
            reg_code = registration.key
            reg_uuid = str(registration.uuid)
            signer = Signer(salt=reg_uuid)
            signed_reg_code = signer.sign(reg_code)
            protocol = 'http'
            if request.is_secure():
                protocol += 's'
            url = '{}://{}{}?reg={}&key={}'.format(
                protocol,
                request.get_host(),
                reverse('ha:reg:step.2'),
                quote(reg_uuid),
                quote(signed_reg_code)
            )
            try:
                registration_mail = EmailMessage(
                    to=[email],
                    from_email=settings.EMAIL_REGISTRATION_FROM,
                    subject=settings.EMAIL_REGISTRATION_SUBJECT,
                    body=get_template('hub_app/registration/reg-email.txt').render({
                        'reg_url': url,
                        'first_name': first_name,
                    })
                )
                registration_mail.send(fail_silently=False)
            except (OSError, ValueError):
                transaction.savepoint_rollback(tx_id)
                form.add_error(
                    None,
                    _("We've been unable to send you an E-Mail at the moment. Please try again later.")
                )
                return self._send_form(request, form)
            transaction.savepoint_commit(tx_id)
        return render(request, self.success_template_name, {}, content_type=self.content_type)


class RegistrationSecondStepView(UserPassesTestMixin, View):
    """
    Second step (Password and OTP)
    """

    raise_exception = True
    content_type = 'text/html'

    bad_link_template_name = 'hub_app/registration/step2-bad-url.html'
    success_template_name = 'hub_app/registration/step2-success.html'
    template_name = 'hub_app/registration/step2.html'

    @csp_update(IMG_SRC='data:')
    def dispatch(self, request, *args, **kwargs):
        return super(RegistrationSecondStepView, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_anonymous

    def _send_form(self, request, form):
        try:
            return render(request, self.template_name, {
                'form': form,
                'totp_secret': b64decode(request.session['registration_step2_totp'].encode('ascii')),
                'username': request.session['registration_step2_username'],
                'user_id': request.session['registration_step2_user_id'],
            }, content_type=self.content_type)
        except KeyError:
            return render(request, self.bad_link_template_name, {}, content_type=self.content_type)

    def get(self, request):
        """
        Handle the GET request
        """
        form = RegistrationStep2UrlForm(request.GET)
        if not form.is_valid():
            return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
        pending_uuid = str(form.cleaned_data['reg'])
        signed_pending_key = form.cleaned_data['key']
        signer = Signer(salt=pending_uuid)
        try:
            pending_key = signer.unsign(signed_pending_key)
        except (BadSignature, ValueError):
            return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
        try:
            pending = PendingRegistration.objects.filter(
                valid_until__gte=now(), user__is_active=True, user__totp_secret__isnull=False
            ).select_related('user').get(uuid=pending_uuid)  # type: PendingRegistration
        except PendingRegistration.DoesNotExist:
            return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
        if pending_key != pending.key:
            return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
        request.session['registration_step2_totp'] = b64encode(pending.user.get_totp_secret()).decode('ascii')
        request.session['registration_step2_username'] = pending.user.username
        request.session['registration_step2_user_id'] = pending.user.id
        reg_form = RegistrationStep2Form(initial={
            'key': signed_pending_key,
            'reg': pending_uuid,
        })
        return self._send_form(request, reg_form)

    def post(self, request):
        """
        Handle the POST request
        """
        form = RegistrationStep2Form(request.POST)
        if not form.is_valid():
            return self._send_form(request, form)
        additional_errors = False
        if form.cleaned_data['password1'] != form.cleaned_data['password2']:
            additional_errors = True
            form.add_error('password2', _('The passwords do not match'))
        if any([
                'registration_step2_user_id' not in request.session,
                'registration_step2_username' not in request.session,
                'registration_step2_totp' not in request.session,
        ]):
            return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
        user = None
        try:
            user = HubUser.objects.get(id=request.session['registration_step2_user_id'])
            validate_password(password=form.cleaned_data['password1'], user=user)
        except HubUser.DoesNotExist:
            return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
        except ValidationError as error:
            additional_errors = True
            form.add_error('password1', error)
        if additional_errors:
            form.add_error('otp', _('Your one time password may be expired, be sure to provide a current one.'))
            return self._send_form(request, form)
        # Check the OTP
        otp = form.cleaned_data['otp']
        if otp not in get_possible_otps(b64decode(request.session['registration_step2_totp'].encode('ascii'))):
            form.add_error('otp', _('Your one time password has expired'))
            form.add_error('password1', _('Please re-enter your password'))
            return self._send_form(request, form)
        # Put it into the database
        with transaction.atomic():
            tx_id = transaction.savepoint()
            try:
                pending = PendingRegistration.objects.filter(
                    valid_until__gte=now(), user__is_active=True, user__totp_secret__isnull=False, user=user
                ).select_related('user').get(uuid=form.cleaned_data['reg'])  # type: PendingRegistration
            except PendingRegistration.DoesNotExist:
                transaction.savepoint_rollback(tx_id)
                return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
            signer = Signer(salt=str(form.cleaned_data['reg']))
            try:
                key = signer.unsign(form.cleaned_data['key'])
            except (BadSignature, ValueError):
                transaction.savepoint_rollback(tx_id)
                return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
            if key != pending.key:
                transaction.savepoint_rollback(tx_id)
                return render(request, self.bad_link_template_name, {}, content_type=self.content_type)
            pending.delete()
            user.set_password(form.cleaned_data['password1'])
            transaction.savepoint_commit(tx_id)
        logout(request)
        return render(request, self.success_template_name, {}, content_type=self.content_type)
