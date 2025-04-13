from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'orders', views.OrderRecordViewSet, basename='order')
router.register(r'metrics', views.StatusMetricsViewSet, basename='metrics')
router.register(r'history', views.StatusHistoryViewSet, basename='history')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
