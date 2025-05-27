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
    permission_classes = []

    def post(self, request):
        try:
            logger.info("درخواست OTP دریافت شد")
            phone = request.data.get("phone")
            password = request.data.get("password")

            if not phone or not password:
                logger.warning("شماره تلفن یا رمز عبور ارائه نشده")
                return Response({"error": "شماره و رمز الزامی است."}, status=400)

            user = User.objects(phone=phone).first()
            if user:
                # کاربر قبلاً ثبت‌نام کرده، باید رمز صحیح بده
                if not user.check_password(password):
                    logger.warning(f"این شماره قبلا وجود داره: {phone}")
                    return Response({"error": "این شماره قبلا وجود داره."}, status=401)
                logger.info(f"کاربر موجود، رمز صحیح است: {phone}")
            else:
                logger.info(f"کاربر جدید: {phone}")

            logger.info(f"در حال تولید کد OTP برای: {phone}")
            code = str(randint(100000, 999999))
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)

            # حذف کدهای قبلی
            deleted_count = OTPCode.objects(phone=phone).delete()
            logger.info(f"{deleted_count} کد قبلی حذف شد")

            # ذخیره کد جدید
            OTPCode(phone=phone, code=code, expires_at=expires_at).save()
            logger.info(f"کد OTP جدید برای {phone} ذخیره شد (انقضا: {expires_at})")
            logger.info(f"کد OTP برای {phone}: {code}")

            if settings.DEBUG:
                logger.debug(f"کد در حالت DEBUG: {code}")

            return Response({"message": "کد تأیید ارسال شد.", "otp": code}, status=200)

        except Exception as e:
            logger.error(f"خطا در تولید OTP: {str(e)}", exc_info=True)
            return Response({"error": "خطای سرور رخ داده است."}, status=500)


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
