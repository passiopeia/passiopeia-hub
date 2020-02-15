"""
Views for registration
"""
from django.contrib.auth import logout
from django.views.generic import TemplateView


class RegistrationFirstStepView(TemplateView):
    """
    First step of the registration
    """

    template_name = 'hub_app/registration/step1.html'
    content_type = 'text/html'

    def dispatch(self, request, *args, **kwargs):
        logout(request)
        return super(RegistrationFirstStepView, self).dispatch(request, *args, **kwargs)
