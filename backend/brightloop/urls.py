from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core Identity, Access & Staff Management
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/staff/', include('apps.staff.urls')),
    path('api/v1/customers/', include('apps.customers.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),

    # Catalog & Subscriptions
    path('api/v1/catalog/', include('apps.catalog.urls')),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    path('api/catalog/', include('apps.catalog.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),

    # Invoicing & Billing
    path('api/v1/billing/', include(('apps.billing.urls', 'billing'), namespace='billing_api')),
    path('billing/', include('apps.billing.urls')),

    # Payments, Portal & Reporting
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/portal/', include('apps.portal.urls')),
    path('api/v1/reports/', include('apps.reporting.urls')),
    path('api/v1/reporting/', include('apps.reporting.urls')),
]
