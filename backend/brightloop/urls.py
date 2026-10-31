from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/portal/', include('apps.portal.urls')),
    path('api/v1/reports/', include('apps.reporting.urls')),
]
