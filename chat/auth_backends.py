# chat/auth_backends.py

import jwt
from chat.models import User
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class MongoJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            phone = payload.get("phone")
            if not phone:
                raise AuthenticationFailed("Invalid token payload: phone not found")

            user = User.objects(phone=phone).first()
            if user is None:
                raise AuthenticationFailed("User not found")
            request.mongo_user = user  # attach user to request
            return (user, None)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")


class IsAuthenticatedMongo(BasePermission):
    """
    فقط کاربرانی که احراز هویت شده‌اند (JWT معتبر دارند) مجاز هستند.
    """

    def has_permission(self, request, view):
        return hasattr(request, "mongo_user") and request.mongo_user is not None


class IsNotBanned(BasePermission):
    """
    فقط کاربرانی که بن نشده‌اند مجاز هستند.
    """

    def has_permission(self, request, view):
        user = getattr(request, "mongo_user", None)
        return user and not getattr(user, "is_banned", False)


class IsRoomCreator(BasePermission):
    """
    فقط سازنده اتاق مجاز به انجام عملیات است (مثلاً حذف یا ویرایش).
    """

    def has_object_permission(self, request, view, obj):
        return str(getattr(obj, "creator", None).id) == str(request.mongo_user.id)


class IsOwner(BasePermission):
    """
    فقط خود کاربر می‌تواند به اطلاعات یا عملیات شخصی خودش دسترسی داشته باشد.
    """

    def has_object_permission(self, request, view, obj):
        return str(getattr(obj, "id", None)) == str(request.mongo_user.id)


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, "mongo_user") and getattr(
            request.mongo_user, "is_admin", False
        )
