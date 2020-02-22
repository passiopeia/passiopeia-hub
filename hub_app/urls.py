"""
URL Config for the hub_app, which is the main app
"""
from django.conf.urls import url
from django.urls import path
from django.views.decorators.cache import never_cache

from hub_app.views.admin import RegenerateOtpSecretView, QrCodeByUser, OtpAssistantView
from hub_app.views.auth import LogoutView, LoginView
from hub_app.views.forgot_credentials import ForgotCredentialsFirstStepView, ForgotCredentialsSecondStepView, \
    ForgotCredentialsThirdStepView, ForgotCredentialsRevealUsername, ForgotCredentialsSetNewPasswordView, \
    ForgotCredentialsRevealNewOtpSecret, ForgotCredentialsConfirmNewOtpSecret
from hub_app.views.home import HomeView
from hub_app.views.registration import RegistrationFirstStepView, RegistrationSecondStepView


FORGOT_CREDENTIALS = ([
    path('step-1', never_cache(ForgotCredentialsFirstStepView.as_view()), name='step.1'),
    url(r'^step-2/(?P<lost>(password|username|otp-secret))$',
        never_cache(ForgotCredentialsSecondStepView.as_view()), name='step.2'),
    path('step-3/<uuid:recovery>/reveal-username', never_cache(ForgotCredentialsRevealUsername.as_view()),
         name='step.3.username'),
    path('step-3/<uuid:recovery>/set-new-password', never_cache(ForgotCredentialsSetNewPasswordView.as_view()),
         name='step.3.password'),
    path('step-3/<uuid:recovery>/reveal-new-otp-secret/confirm',
         never_cache(ForgotCredentialsConfirmNewOtpSecret.as_view()), name='step.3.otp-secret.confirm'),
    path('step-3/<uuid:recovery>/reveal-new-otp-secret', never_cache(ForgotCredentialsRevealNewOtpSecret.as_view()),
         name='step.3.otp-secret'),
    path('step-3/<uuid:recovery>', never_cache(ForgotCredentialsThirdStepView.as_view()),
         name='step.3'),
], 'fc', 'hub_app:auth:fc')


AUTH_URLS = ([
    path('logout', never_cache(LogoutView.as_view()), name='logout'),
    path('login', never_cache(LoginView.as_view()), name='login'),
    path('forgot-credentials/', FORGOT_CREDENTIALS),
], 'auth', 'hub_app:auth')


ADMIN_URLS = ([
    url(
        r'^actions/regenerate-otp/(?P<user_id>\d+)$',
        never_cache(RegenerateOtpSecretView.as_view()),
        name='actions.regenerate-otp-secret'
    ),
    url(
        r'^views/otp-qr/(?P<user_id>\d+)\.(?P<file_type>svg|png)$',
        never_cache(QrCodeByUser.as_view()),
        name='views.qr'
    ),
    url(
        r'^views/otp-assistant/(?P<user_id>\d+)$',
        never_cache(OtpAssistantView.as_view()),
        name='views.otp-assistant'
    ),
], 'admin', 'hub_app:admin')


REGISTRATION_URLS = ([
    path('step-1', never_cache(RegistrationFirstStepView.as_view()), name='step.1'),
    path('step-2', never_cache(RegistrationSecondStepView.as_view()), name='step.2'),
], 'reg', 'hub_app:reg')


urlpatterns = [  # pylint: disable=invalid-name
    path('admin/', ADMIN_URLS),
    path('auth/', AUTH_URLS),
    path('register/', REGISTRATION_URLS),
    url(r'^$', HomeView.as_view(), name='home'),
]
