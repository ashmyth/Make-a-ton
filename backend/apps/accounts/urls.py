from django.urls import path
from .views import CurrentUserView, LoginView, LogoutView, CSRFTokenView

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="auth-me"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("csrf/", CSRFTokenView.as_view(), name="auth-csrf"),
]
