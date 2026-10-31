from django.urls import path
from .views import DashboardMetricsView, InvoiceReportView, PaymentReportView

urlpatterns = [
    path("dashboard/", DashboardMetricsView.as_view(), name="report-dashboard"),
    path("invoices/", InvoiceReportView.as_view(), name="report-invoices"),
    path("payments/", PaymentReportView.as_view(), name="report-payments"),
]
