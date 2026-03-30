from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register_user_view, name="register_user"),
    path("register/driver/", views.register_driver_view, name="register_driver"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
