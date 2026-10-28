"""URL configuration for decware_order_tracker project."""
from django.contrib import admin
from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/orders/', include('orders.urls')),  # Orders API endpoints
    path('api-auth/', include('rest_framework.urls')),  # DRF browsable API auth
    path('api-docs/', views.api_landing_page, name='api-docs'),  # API documentation page
]

# Serve React frontend - catch all other routes and let React handle routing.
# API and admin paths are excluded so a mistyped or slash-less API URL gets a
# 404 or APPEND_SLASH redirect instead of the React page.
urlpatterns += [
    re_path(r'^(?!api/|api-auth/|api-docs/|admin/).*', views.index, name='index'),
]
