"""
Views for authentication
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from hub_app.forms.auth import UsernamePasswordOtpForm
from hub_app.navlib.next_url import get_next


class LogoutView(View):
    """
    Logout View
    """

    http_method_names = ['get']

    @staticmethod
    def _logout(request):
        logout(request)
        messages.add_message(request, messages.SUCCESS, _('Logout successful.'))
        return redirect(settings.LOGOUT_REDIRECT_URL)

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Just handle the GET request
        """
        return LogoutView._logout(request)


class LoginView(View):
    """
    Login View
    """

    http_method_names = ['get', 'post']
    template_name = 'hub_app/auth/login.html'
    content_type = 'text/html'

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        If the user is logged on, it must logout first. This is enforced here.
        """
        if request.user.is_authenticated:
            logout(request)
            return redirect(reverse_lazy('ha:auth:login'), permanent=False)
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def _show_form(self, request: HttpRequest, form: UsernamePasswordOtpForm = UsernamePasswordOtpForm()):
        """
        Send the form to the client
        """
        return render(request, self.template_name, {
            'form': form,
            'next_url': get_next(request),
        }, content_type=self.content_type)

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        On GET-Request, only send the form
        """
        return self._show_form(request)

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Handle the Login
        """
        form = UsernamePasswordOtpForm(request.POST)
        if not form.is_valid():
            return self._show_form(request, form)
        data = form.clean()
        user = authenticate(
            request,
            username=data['username'],
            password=data['password'],
            one_time_pw=data['otp']
        )
        if user is None:
            form.add_error(None, _('Username or password wrong, or one time password invalid.'))
            return self._show_form(request, form)
        login(request, user)
        messages.add_message(request, messages.SUCCESS, _('Hey %(user)s, welcome to Passiopeia Hub!') % {
            'user': user.first_name
        })
        next_url = get_next(request)
        if next_url is None:
            next_url = settings.LOGIN_REDIRECT_URL
        return redirect(next_url, permanent=False)


class ForgotCredentialsView(TemplateView):
    """
    The Password Reset procedure
    """

    content_type = 'text/html'
    template_name = 'hub_app/auth/forgot-credentials.html'
    http_method_names = ['get']

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            return redirect(reverse_lazy('ha:auth:forgot-credentials'), permanent=False)
        return super(ForgotCredentialsView, self).dispatch(request, *args, **kwargs)
