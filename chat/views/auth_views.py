import logging
from datetime import datetime, timedelta, timezone
from random import randint

import jwt
from chat.models import OTPCode, User
from chat.utils import generate_tokens
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# تنظیمات لاگ‌گیری
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("auth.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class RequestOTPWithPasswordView(APIView):
    def post(self, request):
        try:
            logger.info("دریافت درخواست OTP - شروع پردازش")
            phone = request.data.get("phone")
            password = request.data.get("password")

            # اعتبارسنجی اولیه
            if not phone or not password:
                logger.error("فیلدهای ضروری پر نشده")
                return Response(
                    {"error": "شماره و رمز الزامی است"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.debug(f"پردازش برای شماره: {phone}")

            # تولید کد OTP
            code = str(randint(100000, 999999))
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)

            # ذخیره در دیتابیس
            try:
                OTPCode.objects(phone=phone).delete()
                otp = OTPCode(phone=phone, code=code, expires_at=expires_at)
                otp.save()
                logger.info(f"کد OTP برای {phone} ذخیره شد")
            except Exception as db_error:
                logger.error(f"خطای دیتابیس: {str(db_error)}")
                return Response(
                    {"error": "خطا در ذخیره کد تأیید"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # در محیط توسعه کد را نمایش دهید
            if settings.DEBUG:
                logger.debug(f"کد OTP (فقط توسعه): {code}")
                print(f"\n--- کد OTP برای {phone}: {code} ---\n")

            return Response({"message": "کد تأیید ارسال شد"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.critical(f"خطای غیرمنتظره: {str(e)}", exc_info=True)
            return Response(
                {"error": "خطای سرور رخ داده است"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyOTPAndLoginView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            logger.info("درخواست تأیید OTP دریافت شد")
            phone = request.data.get("phone")
            password = request.data.get("password")
            code = request.data.get("code")

            if not all([phone, password, code]):
                logger.warning("فیلدهای ضروری ارائه نشده")
                return Response({"error": "همه فیلدها الزامی هستند."}, status=400)

            logger.info(f"جستجوی کد OTP برای {phone}")
            otp = OTPCode.objects(phone=phone, code=code).first()

            if not otp:
                logger.warning(f"کد OTP نامعتبر برای {phone}")
                return Response({"error": "کد اشتباه یا منقضی شده."}, status=401)

            expires_at = (
                otp.expires_at.replace(tzinfo=timezone.utc)
                if otp.expires_at.tzinfo is None
                else otp.expires_at
            )

            if expires_at < datetime.now(timezone.utc):
                logger.warning(f"کد منقضی شده برای {phone} (تاریخ انقضا: {expires_at})")
                return Response({"error": "کد اشتباه یا منقضی شده."}, status=401)

            otp.delete()
            logger.info(f"کد OTP برای {phone} مصرف شد")

            user = User.objects(phone=phone).first()

            if not user:
                logger.info(f"کاربر جدید با شماره {phone} در حال ایجاد است")
                user = User(username=phone, phone=phone)
                user.set_password(password)
                user.save()
                logger.info(f"کاربر جدید ایجاد شد: {user.id}")
            else:
                if not user.check_password(password):
                    logger.warning(f"رمز عبور نادرست برای کاربر {phone}")
                    return Response({"error": "رمز اشتباه است."}, status=401)

            access, refresh = generate_tokens(user)
            logger.info(f"ورود موفق برای کاربر {phone}")
            return Response({"access": access, "refresh": refresh})

        except Exception as e:
            logger.error(f"خطا در تأیید OTP: {str(e)}", exc_info=True)
            return Response({"error": "خطای سرور رخ داده است."}, status=500)


class RefreshTokenView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            logger.info("درخواست تمدید توکن دریافت شد")
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                logger.warning("توکن رفرش ارائه نشده")
                return Response({"error": "توکن رفرش الزامی است."}, status=400)

            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
            )

            if payload.get("type") != "refresh":
                logger.warning("نوع توکن نامعتبر")
                return Response({"error": "توکن نامعتبر است."}, status=400)

            user_phone = payload.get("phone")
            user = User.objects(phone=user_phone).first()

            if not user:
                logger.warning(f"کاربر با شماره {user_phone} یافت نشد")
                return Response({"error": "کاربر یافت نشد."}, status=404)

            access_token, _ = generate_tokens(user)
            logger.info(f"توکن جدید برای کاربر {user_phone} ایجاد شد")
            return Response({"access": access_token})

        except jwt.ExpiredSignatureError:
            logger.warning("توکن رفرش منقضی شده")
            return Response({"error": "توکن رفرش منقضی شده است."}, status=401)
        except jwt.InvalidTokenError as e:
            logger.error(f"توکن نامعتبر: {str(e)}")
            return Response({"error": "توکن نامعتبر است."}, status=400)
        except Exception as e:
            logger.error(f"خطای ناشناخته در تمدید توکن: {str(e)}", exc_info=True)
            return Response({"error": "خطای سرور رخ داده است."}, status=500)
