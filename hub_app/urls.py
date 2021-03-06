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
from hub_app.views.my_account import MyAccountOverviewView, MyAccountCredentialsOverviewView, \
    MyAccountDatabasesOverviewView, MyAccountPersonalOverviewView, MyAccountCredentialsPasswordView, \
    MyAccountCredentialsOtpSecretView, MyAccountPersonalNameView, MyAccountPersonalEMailView, \
    MyAccountPersonalEMailVerifyView
from hub_app.views.registration import RegistrationFirstStepView, RegistrationSecondStepView
from hub_app.views.support import TestYourAppView

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


MY_ACCOUNT_URLS = ([
    path('credentials/password', MyAccountCredentialsPasswordView.as_view(), name='credentials.password'),
    path('credentials/otp-secret', MyAccountCredentialsOtpSecretView.as_view(), name='credentials.otp-secret'),
    path('credentials', MyAccountCredentialsOverviewView.as_view(), name='credentials'),
    path('databases', MyAccountDatabasesOverviewView.as_view(), name='databases'),
    path('personal/name', MyAccountPersonalNameView.as_view(), name='personal.name'),
    path('personal/email', MyAccountPersonalEMailView.as_view(), name='personal.email'),
    path('personal/email/<uuid:change>', MyAccountPersonalEMailVerifyView.as_view(), name='personal.email.verify'),
    path('personal', MyAccountPersonalOverviewView.as_view(), name='personal'),
    path('', MyAccountOverviewView.as_view(), name='overview'),
], 'acc', 'hub_app:acc')


SUPPORT_URLS = ([
    path('test-your-app', TestYourAppView.as_view(), name='test-your-app'),
], 'supp', 'hub_app:supp')


urlpatterns = [  # pylint: disable=invalid-name
    path('admin/', ADMIN_URLS),
    path('auth/', AUTH_URLS),
    path('register/', REGISTRATION_URLS),
    path('my-account/', MY_ACCOUNT_URLS),
    path('support/', SUPPORT_URLS),
    url(r'^$', HomeView.as_view(), name='home'),
]
