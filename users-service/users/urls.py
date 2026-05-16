from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    LogoutView,
    InternalUserDetailView,
)

urlpatterns = [
    # Public endpoints
    path("register/",           RegisterView.as_view(),         name="register"),
    path("login/",              LoginView.as_view(),            name="login"),
    path("logout/",             LogoutView.as_view(),           name="logout"),
    path("token/refresh/",      TokenRefreshView.as_view(),     name="token-refresh"),

    # Authenticated endpoints
    path("profile/",            ProfileView.as_view(),          name="profile"),

    # Internal endpoints (called by other microservices only)
    path("internal/<uuid:user_id>/", InternalUserDetailView.as_view(), name="internal-user"),
]
