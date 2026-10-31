from django.urls import path

from . import views

urlpatterns = [path("download/", views.download_register, name="register-download")]
