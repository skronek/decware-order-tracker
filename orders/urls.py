from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

router = DefaultRouter()
router.register(r'orders', views.OrderRecordViewSet, basename='order')
router.register(r'history', views.StatusHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
]
