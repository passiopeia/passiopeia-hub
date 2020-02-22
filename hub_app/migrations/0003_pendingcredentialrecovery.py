from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import hub_app.authlib.forgot_credentials
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('hub_app', '0002_pendingregistration'),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingCredentialRecovery',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='UUID')),
                ('recovery_type', models.CharField(choices=[('username', 'Forgot my Username'), ('password', 'Forgot my Password'), ('otp-secret', 'Lost my OTP Secret')], max_length=16)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created')),
                ('valid_until', models.DateTimeField(default=hub_app.authlib.forgot_credentials.get_recovery_max_validity, verbose_name='Valid Until')),
                ('key', models.CharField(default=hub_app.authlib.forgot_credentials.get_recovery_key, max_length=255, verbose_name='Credential Recovery Key')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Pending Credential Recovery',
                'verbose_name_plural': 'Pending Credential Recoveries',
                'permissions': (),
                'default_permissions': ('add', 'change', 'delete'),
            },
        ),
    ]
