# # chat/views.py
# from datetime import datetime, timedelta
# from tokenize import generate_tokens

# import jwt
# from django.conf import settings
# from mongoengine.errors import NotUniqueError
# from rest_framework import status, viewsets
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.views import APIView

# from .auth_backends import IsAuthenticatedMongo, IsNotBanned, IsRoomCreator
# from .models import Challenge, ChallengeResponse, Message, Room, User
# from .serializers import (
#     ChallengeResponseSerializer,
#     ChallengeSerializer,
#     MessageSerializer,
#     RoomSerializer,
# )


# class RoomViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticatedMongo, IsNotBanned]

#     def list(self, request):
#         rooms = Room.objects(is_active=True)
#         serializer = RoomSerializer(rooms, many=True)
#         return Response(serializer.data)

#     def retrieve(self, request, pk=None):
#         room = Room.objects(id=pk).first()
#         if not room:
#             return Response(
#                 {"detail": "اتاق پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
#             )
#         return Response(RoomSerializer(room).data)

#     def create(self, request):
#         serializer = RoomSerializer(data=request.data)
#         if serializer.is_valid():
#             room = Room(**serializer.validated_data)
#             room.created_at = datetime.utcnow()
#             room.creator = request.mongo_user
#             room.save()
#             return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def destroy(self, request, pk=None):
#         room = Room.objects(id=pk).first()
#         if not room:
#             return Response(status=status.HTTP_404_NOT_FOUND)
#         self.check_object_permissions(request, room)  # بررسی مالکیت
#         room.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

#     def get_permissions(self):
#         if self.action in ["destroy"]:
#             return [IsAuthenticatedMongo(), IsNotBanned(), IsRoomCreator()]
#         return super().get_permissions()


# class ChallengeViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticatedMongo, IsNotBanned]

#     def list(self, request):
#         challenges = Challenge.objects()
#         serializer = ChallengeSerializer(challenges, many=True)
#         return Response(serializer.data)

#     def create(self, request):
#         serializer = ChallengeSerializer(data=request.data)
#         if serializer.is_valid():
#             challenge = Challenge(**serializer.validated_data)
#             challenge.created_at = datetime.utcnow()
#             challenge.save()
#             return Response(
#                 ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class MessageViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticatedMongo, IsNotBanned]

#     def list(self, request):
#         messages = Message.objects()
#         serializer = MessageSerializer(messages, many=True)
#         return Response(serializer.data)

#     def create(self, request):
#         serializer = MessageSerializer(data=request.data)
#         if serializer.is_valid():
#             message = Message(**serializer.validated_data)
#             message.user_id = str(request.mongo_user.id)
#             message.save()
#             return Response(
#                 MessageSerializer(message).data, status=status.HTTP_201_CREATED
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=["post"])
#     def like(self, request, pk=None):
#         message = Message.objects(id=pk).first()
#         user_id = str(request.mongo_user.id)
#         if message and user_id not in getattr(message, "likes", []):
#             message.likes = getattr(message, "likes", []) + [user_id]
#             message.save()
#         return Response(MessageSerializer(message).data)

#     @action(detail=True, methods=["post"])
#     def report(self, request, pk=None):
#         message = Message.objects(id=pk).first()
#         if message:
#             message.is_reported = True
#             message.save()
#         return Response({"reported": True})


# class ChallengeResponseViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticatedMongo, IsNotBanned]

#     def create(self, request):
#         serializer = ChallengeResponseSerializer(data=request.data)
#         if serializer.is_valid():
#             try:
#                 response = ChallengeResponse(**serializer.validated_data)
#                 response.answered_at = datetime.utcnow()
#                 response.user = request.mongo_user
#                 response.save()
#                 return Response(
#                     ChallengeResponseSerializer(response).data,
#                     status=status.HTTP_201_CREATED,
#                 )
#             except NotUniqueError:
#                 return Response(
#                     {"error": "شما قبلاً پاسخ داده‌اید."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class PhoneAuthView(APIView):
#     permission_classes = []

#     def post(self, request):
#         phone = request.data.get("phone")
#         password = request.data.get("password")

#         if not phone:
#             return Response(
#                 {"error": "شماره تلفن الزامی است."}, status=status.HTTP_400_BAD_REQUEST
#             )

#         user = User.objects(phone=phone).first()

#         # اگر کاربر وجود نداشت، خودکار بسازش و پسورد هش شده ذخیره کن
#         if not user:
#             user = User(username=phone, phone=phone)
#             if password:
#                 user.set_password(password)
#             user.save()
#         else:
#             # اگر پسورد ارسال شده، بررسی کن
#             if password:
#                 if not user.check_password(password):
#                     return Response(
#                         {"error": "نام کاربری یا رمز عبور اشتباه است."},
#                         status=status.HTTP_401_UNAUTHORIZED,
#                     )
#             else:
#                 return Response(
#                     {"error": "رمز عبور الزامی است."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#         payload = {
#             "phone": user.phone,
#             "exp": datetime.utcnow() + timedelta(days=5),
#             "iat": datetime.utcnow(),
#         }
#         token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
#         return Response({"token": token})


# class RefreshTokenView(APIView):
#     permission_classes = []

#     def post(self, request):
#         refresh_token = request.data.get("refresh")

#         try:
#             payload = jwt.decode(
#                 refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
#             )
#             if payload.get("type") != "refresh":
#                 return Response(
#                     {"error": "توکن نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
#                 )

#             user = User.objects(phone=payload["phone"]).first()
#             if not user:
#                 return Response(
#                     {"error": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND
#                 )

#             access_token, _ = generate_tokens(user)
#             return Response({"access": access_token})

#         except jwt.ExpiredSignatureError:
#             return Response(
#                 {"error": "توکن رفرش منقضی شده است."},
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )
#         except jwt.InvalidTokenError:
#             return Response(
#                 {"error": "توکن نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
#             )
