"""
URL Config for the hub_app, which is the main app
"""
from django.conf.urls import url

from hub_app.views.home import HomeView


urlpatterns = [  # pylint: disable=invalid-name
    url(r'^$', HomeView.as_view(), name='home'),
]
