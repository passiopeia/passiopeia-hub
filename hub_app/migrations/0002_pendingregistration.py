from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import hub_app.reglib.key
import hub_app.reglib.validity
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('hub_app', '0001_basic_user_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingRegistration',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='UUID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created')),
                ('valid_until', models.DateTimeField(default=hub_app.reglib.validity.get_registration_max_validity, verbose_name='Valid Until')),
                ('key', models.CharField(default=hub_app.reglib.key.get_registration_key, max_length=255, verbose_name='Registration Key')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Pending Registration',
                'verbose_name_plural': 'Pending Registrations',
                'permissions': (),
                'default_permissions': ('add', 'change', 'delete'),
            },
        ),
    ]
