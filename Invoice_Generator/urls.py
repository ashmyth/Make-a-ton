from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("staff/invoices/", views.invoice_list, name="invoice_list"),
    path("staff/invoices/<uuid:pk>/", views.invoice_detail, name="invoice_detail"),
    path("staff/invoices/<uuid:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("staff/invoices/<uuid:pk>/send/", views.invoice_send, name="invoice_send"),
]
