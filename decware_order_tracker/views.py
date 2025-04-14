from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache

# Serve the React frontend
index = never_cache(TemplateView.as_view(template_name='index.html'))

def api_landing_page(request):
    """
    View to serve the API landing page when React frontend is not available
    """
    context = {
        'debug': settings.DEBUG
    }
    return render(request, 'api_landing.html', context)
