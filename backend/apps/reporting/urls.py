from django.urls import path
from .views import (
    DashboardMetricsView,
    InvoiceReportView,
    PaymentReportView,
    ExportInvoicesXlsxView,
    ExportPaymentsXlsxView,
)

urlpatterns = [
    path("dashboard/", DashboardMetricsView.as_view(), name="report-dashboard"),
    path("invoices/", InvoiceReportView.as_view(), name="report-invoices"),
    path("invoices/export/", ExportInvoicesXlsxView.as_view(), name="report-invoices-export"),
    path("payments/", PaymentReportView.as_view(), name="report-payments"),
    path("payments/export/", ExportPaymentsXlsxView.as_view(), name="report-payments-export"),
]


