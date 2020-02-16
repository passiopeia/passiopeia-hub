"""
Additional Admin Views
"""
from base64 import b32encode

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from hub_app.authlib.crypt import SymmetricCrypt
from hub_app.authlib.totp.qr import create_png_qr_code, create_transparent_svg_qr_code
from hub_app.authlib.totp.token import create_random_totp_secret
from hub_app.models import HubUser
from hub_app.navlib.next_url import get_next


class QrCodeByUser(PermissionRequiredMixin, View):
    """
    Show User's QR Code
    """

    http_method_names = ['get']
    permission_required = (
        'hub_app.change_hubuser',
    )
    raise_exception = True

    actions = {
        'png': (lambda d, u: create_png_qr_code(u, d, block_size=4), 'image/png'),
        'svg': (lambda d, u: create_transparent_svg_qr_code(u, d, block_size=64), 'image/svg+xml'),
    }

    def get(self, request, user_id: int, file_type: str):
        """
        Handle GET
        """
        (method, content_type) = self.actions[file_type]
        try:
            user_obj = HubUser.objects.get(id=user_id)  # type: HubUser
        except HubUser.DoesNotExist:
            raise Http404()
        if not user_obj.totp_secret:
            raise Http404()
        qr_code = method(b32encode(SymmetricCrypt().decrypt(user_obj.totp_secret)), user_obj.username)
        response = HttpResponse(content_type=content_type)
        qr_code.save(response)
        return response


class OtpAssistantView(PermissionRequiredMixin, TemplateView):
    """
    Show the OTP assistant window
    """

    http_method_names = ['get']
    permission_required = (
        'hub_app.change_hubuser',
    )
    raise_exception = True

    template_name = 'hub_app/admin/dialogs/otp_assistant.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id', None)
        if not user_id:  # pragma: no cover
            raise Http404()
        try:
            user_obj = HubUser.objects.get(id=user_id)  # type: HubUser
        except HubUser.DoesNotExist:
            raise Http404()
        context['username'] = user_obj.username
        has_secret = user_obj.totp_secret is not None and len(user_obj.totp_secret) > 0
        context['has_secret'] = has_secret
        if has_secret:
            context['otp_secret'] = b32encode(SymmetricCrypt().decrypt(user_obj.totp_secret)).decode('us-ascii')
        return context


class RegenerateOtpSecretView(PermissionRequiredMixin, View):
    """
    Regenerate the secret for a user
    """

    http_method_names = ['get']
    permission_required = (
        'hub_app.change_hubuser',
    )
    raise_exception = True

    def get(self, request, user_id: int):
        """
        Handle GET
        """
        try:
            user_obj = HubUser.objects.get(id=user_id)
        except HubUser.DoesNotExist:
            raise Http404()
        user_obj.set_totp_secret(create_random_totp_secret())
        user_obj.save()
        next_page = get_next(request)
        if next_page is not None:
            return redirect(next_page, permanent=False)
        return JsonResponse({
            'status': True
        })
