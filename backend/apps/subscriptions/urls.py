from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuotationTemplateViewSet, QuotationViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'templates', QuotationTemplateViewSet, basename='quotation-template')
router.register(r'quotations', QuotationViewSet, basename='quotation')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]
