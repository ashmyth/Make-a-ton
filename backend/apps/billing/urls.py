from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<uuid:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<uuid:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("invoices/<uuid:pk>/send/", views.invoice_send, name="invoice_send"),
    path("invoices/<uuid:pk>/cancel/", views.invoice_cancel, name="invoice_cancel"),
]
