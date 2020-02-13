"""
URL Config for the hub_app, which is the main app
"""
from django.conf.urls import url
from django.urls import path
from django.views.decorators.cache import never_cache

from hub_app.views.auth import LogoutView, LoginView, ResetPasswordView
from hub_app.views.home import HomeView


AUTH_URLS = ([
    path('logout', never_cache(LogoutView.as_view()), name='logout'),
    path('login', never_cache(LoginView.as_view()), name='login'),
    path('reset-password', never_cache(ResetPasswordView.as_view()), name='reset-password'),
], 'auth', 'hub_app')

urlpatterns = [  # pylint: disable=invalid-name
    path('auth/', AUTH_URLS),
    url(r'^$', HomeView.as_view(), name='home'),
]
