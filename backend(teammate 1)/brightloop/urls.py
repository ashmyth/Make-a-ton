from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/staff/", include("apps.staff.urls")),
    path("api/v1/customers/", include("apps.customers.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
