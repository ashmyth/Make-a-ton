from django.urls import path
from .views import (
    PortalOverviewView,
    PortalSubscriptionListView,
    PortalInvoiceListView,
    PortalInvoiceDetailView,
    PortalInvoiceDownloadView,
    PortalPaymentListView,
    PortalRequestListCreateView,
    PortalProfileView,
)

urlpatterns = [
    path("overview/", PortalOverviewView.as_view(), name="portal-overview"),
    path("subscriptions/", PortalSubscriptionListView.as_view(), name="portal-subscriptions"),
    path("invoices/", PortalInvoiceListView.as_view(), name="portal-invoices"),
    path("invoices/<uuid:id>/", PortalInvoiceDetailView.as_view(), name="portal-invoice-detail"),
    path("invoices/<uuid:id>/download/", PortalInvoiceDownloadView.as_view(), name="portal-invoice-download"),
    path("payments/", PortalPaymentListView.as_view(), name="portal-payments"),
    path("requests/", PortalRequestListCreateView.as_view(), name="portal-requests"),
    path("profile/", PortalProfileView.as_view(), name="portal-profile"),
]

