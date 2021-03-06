"""hub URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path, include, reverse_lazy
from django.views.generic import RedirectView

from hub_app.admin import admin_site

urlpatterns = [  # pylint: disable=invalid-name
    path('admin/', admin_site.urls, name='admin'),
    path('client-configuration/i18n/', include('django.conf.urls.i18n')),
    path('hub/', include(('hub_app.urls', 'hub_app'), namespace='ha')),
    path('schema/', include(('hub_json_schema.urls', 'hub_json_schema'), namespace='json')),
    url('^$', RedirectView.as_view(url=reverse_lazy('ha:home'), permanent=False), name='index'),
]
