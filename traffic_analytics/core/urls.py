from django.conf import settings
from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views

from ui.views import Signup, Login, Logout, PasswordResetView
from vehicle_counter.views import Home
from django.shortcuts import redirect

urlpatterns = [
    path("inicio/", Home.as_view(), name="home"),
    path("", lambda req: redirect('/inicio/')),
    path("vehicle_counter/", include(("vehicle_counter.urls", "vehicle_counter"), namespace="vehicle_counter")),
    path("login/", Login.as_view(), name="login"),
    path("logout/", Logout.as_view(), name="logout"),
    path("password_reset/<uid>/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("admin/", admin.site.urls),
]

if settings.SERVE_STATIC:
    # serve staticfiles via runserver
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
