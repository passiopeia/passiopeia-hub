"""
User Admin
"""
from uuid import uuid4

from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _


class ReadOnlySecretWidget(forms.Widget):
    """
    Widget for OTP secret
    """

    template_name = 'hub_app/admin/widgets/readonlysecretwidget.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        field_description = {
            'value_label': _('OTP Secret'),
            'otp_assistant': _('OTP Assistant'),
            'selector': uuid4(),
            'value': _('Use Assistant'),
        }
        context['fd'] = field_description
        return context


class ReadOnlySecretField(forms.Field):
    """
    Field for OTP secret
    """

    widget = ReadOnlySecretWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)

    def bound_data(self, data, initial):
        return initial

    def has_changed(self, initial, data):
        return False


class UserAdminForm(UserChangeForm):
    """
    User Admin Form
    """

    get_totp_secret_length = ReadOnlySecretField(
        help_text=_('OTP Secrets are managed through the OTP Assistant. Click the link above to use it.'),
        label=_('One Time Password Secret')
    )


class HubUserAdmin(UserAdmin):
    """
    The HubUser Admin
    """

    form = UserAdminForm

    ordering = ('last_name', 'first_name', 'username',)

    list_display = (
        'username', 'last_name', 'first_name', 'email',
        'is_active', 'is_staff', 'is_superuser',
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Login Configuration'), {
            'fields': (
                'is_active',
            )
        }),
    )

    fieldsets = UserAdmin.fieldsets + (
        (_('One Time Password'), {
            'fields': (
                'get_totp_secret_length',
            )
        }),
    )

    readonly_fields = UserAdmin.readonly_fields + (
        'id', 'last_login',
    )
