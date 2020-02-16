"""
Admin for Burned OTPs
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class PendingRegistrationAdmin(admin.ModelAdmin):
    """
    Pending Registration Admin
    """

    list_display = (
        'uuid',
        'user',
        'created',
        'valid_until',
    )

    ordering = ('uuid',)

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
        (_('Validity'), {
            'fields': (
                'created',
                'valid_until',
            ),
        }),
        (_('Key'), {
            'fields': (
                'key',
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover  # No end-user use-case for that
        if obj:
            return self.readonly_fields + ('user', 'created',)
        return self.readonly_fields
