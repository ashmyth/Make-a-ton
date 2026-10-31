from django.urls import path
from .views import PaymentListCreateView, PaymentDetailView, PaymentReverseView

urlpatterns = [
    path("", PaymentListCreateView.as_view(), name="payment-list-create"),
    path("<uuid:id>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("<uuid:id>/reverse/", PaymentReverseView.as_view(), name="payment-reverse"),
]

