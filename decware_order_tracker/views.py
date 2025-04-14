from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
import os
import logging

logger = logging.getLogger(__name__)

# Serve the React frontend
@never_cache
def index(request):
    """
    View to serve the React frontend
    """
    try:
        # First try to serve the React app from the templates directory
        return render(request, 'react/index.html')
    except Exception as e:
        logger.error(f"Error serving React frontend: {str(e)}")
        return api_landing_page(request)

def api_landing_page(request):
    """
    View to serve the API landing page when React frontend is not available
    """
    context = {
        'debug': settings.DEBUG
    }
    return render(request, 'api_landing.html', context)
