from rest_framework.routers import SimpleRouter

from .views import StaffViewSet

router = SimpleRouter()
router.register("", StaffViewSet, basename="staff")
urlpatterns = router.urls
