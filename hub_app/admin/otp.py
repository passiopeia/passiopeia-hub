"""
Admin for Burned OTPs
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class BurnedOtpAdmin(admin.ModelAdmin):
    """
    Burned OTP Admin
    """

    list_display = (
        'user',
        'token',
        'burned_timestamp',
        'uuid',
    )

    ordering = ('-burned_timestamp',)

    readonly_fields = (
        'uuid',
    )

    fieldsets = (
        (_('Identification'), {
            'fields': (
                'uuid',
            ),
        }),
        (_('User'), {
            'fields': (
                'user',
            ),
        }),
        (_('Token Data'), {
            'fields': (
                'token',
                'burned_timestamp',
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover  # No end-user use-case for that
        if obj:
            return self.readonly_fields + ('user', 'token', 'burned_timestamp',)
        return self.readonly_fields
