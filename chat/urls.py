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
from chat.views.home import home
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

# تنظیمات پیشرفته برای Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Chatbot API",
        default_version="v1",
        description="مستندات کامل API چت‌بات",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

# Router برای API ViewSets
router = DefaultRouter()
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"challenges", ChallengeViewSet, basename="challenge")
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"responses", ChallengeResponseViewSet, basename="response")

urlpatterns = [
    # صفحه اصلی
    path("", home, name="home"),
    # API Endpoints
    path("api/", include(router.urls)),
    # احراز هویت
    path(
        "auth/request-code/", RequestOTPWithPasswordView.as_view(), name="request_code"
    ),
    path("auth/verify-code/", VerifyOTPAndLoginView.as_view(), name="verify_otp_login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    # پنل مدیریت
    path("admin/login/", admin_login_view, name="admin_login"),
    path("admin/logout/", admin_logout_view, name="admin_logout"),
    path("admin/users/", user_admin_panel, name="user_admin_panel"),
    path(
        "admin/users/<str:user_id>/toggle-ban/", toggle_ban_user, name="toggle_ban_user"
    ),
    path("admin/users/<str:user_id>/delete/", delete_user, name="delete_user"),
    # مستندات API
    re_path(
        r"^aswagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema_json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema_swagger_ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema_redoc",
    ),
]

# فقط در حالت توسعه فایل‌های استاتیک سرویس دهی شوند
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
