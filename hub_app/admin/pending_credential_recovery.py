"""
Admin for Pending Credential Recoveries
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class PendingCredentialRecoveryAdmin(admin.ModelAdmin):
    """
    Pending Credential Recovery Admin
    """

    list_display = (
        'uuid',
        'user',
        'recovery_type',
        'created',
        'valid_until',
    )

    ordering = ('uuid',)

    readonly_fields = (
        'uuid',
    )

    fieldsets = (
        (_('Base Data'), {
            'fields': (
                'uuid', 'user',
                'recovery_type',
                'created', 'valid_until',
            ),
        }),
        (_('Key'), {'fields': ('key',)}),
    )

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover  # No end-user use-case for that
        if obj:
            return self.readonly_fields + ('user', 'created', 'key', 'recovery_type')
        return self.readonly_fields
