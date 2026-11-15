from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("wordmark/", views.wordmark, name="wordmark"),
    path("register/", views.register, name="register"),
    path("register/complete/", views.registration_complete, name="registration_complete"),
    path(
        "login/",
        views.ServiceAwareLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("services/start/", views.service_start, name="service_start"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
]
