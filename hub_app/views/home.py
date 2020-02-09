"""
Landing Page View Implementation
"""

from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    The Landing Page View, based on our template structure
    """

    template_name = 'hub_app/pages/landing-page/welcome.html'
