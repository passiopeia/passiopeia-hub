"""
Views for authentication
"""
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views import View

from hub_app.forms.auth import UsernamePasswordOtpForm


class LogoutView(View):
    """
    Logout View
    """

    http_method_names = ['get']

    @staticmethod
    def _logout(request):
        logout(request)
        messages.add_message(request, messages.SUCCESS, _('Logout successful.'))
        return redirect(reverse_lazy('ha:home'))

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
            return redirect(reverse_lazy('ha:auth:logout'), permanent=False)
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def _show_form(self, request: HttpRequest, form: UsernamePasswordOtpForm = UsernamePasswordOtpForm()):
        """
        Send the form to the client
        """
        return render(request, self.template_name, {
            'form': form
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
        return redirect(reverse_lazy('ha:home'))


class ResetPasswordView(View):
    """
    The Password Reset procedure
    """
