from chat.views.admin_panel import (
    admin_login_view,
    admin_logout_view,
    delete_user,
    toggle_ban_user,
    user_admin_panel,
)
from chat.views.auth_views import (
    RefreshTokenView,
    RequestOTPWithPasswordView,
    VerifyOTPAndLoginView,
)
from chat.views.core_views import (
    ChallengeResponseViewSet,
    ChallengeViewSet,
    MessageViewSet,
    RoomViewSet,
)
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

# Swagger Imports 👇
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

# 📌 تعریف پشتیبانی از JWT در Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Chatbot API",
        default_version="v1",
        description="مستندات کامل API چت‌بات",
        contact=openapi.Contact(email="admin@example.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)


# Router Definition
router = DefaultRouter()
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"challenges", ChallengeViewSet, basename="challenge")
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"responses", ChallengeResponseViewSet, basename="response")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "auth/request-code/", RequestOTPWithPasswordView.as_view(), name="request_code"
    ),
    path("auth/verify-code/", VerifyOTPAndLoginView.as_view(), name="verify_otp_login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    # Admin Panel URLs
    path("admin/login/", admin_login_view, name="admin_login"),
    path("admin/logout/", admin_logout_view, name="admin_logout"),
    path("admin/users/", user_admin_panel, name="user_admin_panel"),
    path(
        "admin/users/<str:user_id>/toggle-ban/", toggle_ban_user, name="toggle_ban_user"
    ),
    path("admin/users/<str:user_id>/delete/", delete_user, name="delete_user"),
    # 📄 Swagger & ReDoc URLs
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
