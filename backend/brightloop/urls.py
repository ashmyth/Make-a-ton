from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/v1/catalog/', include('apps.catalog.urls')),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    path('api/catalog/', include('apps.catalog.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),

    path('admin/', admin.site.urls),
    path('billing/', include('apps.billing.urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/portal/', include('apps.portal.urls')),
    path('api/v1/reports/', include('apps.reporting.urls')),
]
