from django.shortcuts import render
from django.conf import settings

def index(request):
    """
    View to serve the React frontend
    """
    context = {
        'debug': settings.DEBUG
    }
    return render(request, 'index.html', context)
