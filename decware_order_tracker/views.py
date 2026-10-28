from django.shortcuts import render
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.views.decorators.cache import never_cache
import logging

logger = logging.getLogger(__name__)


@never_cache
def index(request):
    """
    Serves the React frontend. Its index.html is copied into the templates
    directory by heroku-build.sh; without a build, show the API landing page.
    """
    try:
        return render(request, 'react/index.html')
    except TemplateDoesNotExist:
        logger.error("React frontend build not found (templates/react/index.html)")
        return api_landing_page(request)


def api_landing_page(request):
    """
    View to serve the API landing page when React frontend is not available
    """
    context = {
        'debug': settings.DEBUG
    }
    return render(request, 'api_landing.html', context)
