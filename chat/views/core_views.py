import logging
from datetime import datetime

from chat.auth_backends import IsAuthenticatedMongo, IsNotBanned, IsRoomCreator
from chat.models import Challenge, ChallengeResponse, Message, Room
from chat.serializers import (
    ChallengeResponseSerializer,
    ChallengeSerializer,
    MessageSerializer,
    RoomSerializer,
)
from mongoengine.errors import NotUniqueError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# تنظیمات پایه برای لاگ‌گیری
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ایجاد handler برای ذخیره لاگ‌ها در فایل
file_handler = logging.FileHandler("chat_views.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def list(self, request):
        logger.info("Listing all active rooms")
        rooms = Room.objects(is_active=True)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        logger.info(f"Retrieving room with id: {pk}")
        room = Room.objects(id=pk).first()
        if not room:
            logger.warning(f"Room not found with id: {pk}")
            return Response(
                {"detail": "اتاق پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(RoomSerializer(room).data)

    def create(self, request):
        logger.info("Creating new room")
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            room = Room(**serializer.validated_data)
            room.created_at = datetime.utcnow()
            room.creator = request.mongo_user
            room.save()
            logger.info(f"Room created successfully with id: {room.id}")
            return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)
        logger.error(f"Room creation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        logger.info(f"Attempting to delete room with id: {pk}")
        room = Room.objects(id=pk).first()
        if not room:
            logger.warning(f"Room not found for deletion with id: {pk}")
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, room)  # بررسی مالکیت
        room.delete()
        logger.info(f"Room deleted successfully with id: {pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action in ["destroy"]:
            return [IsAuthenticatedMongo(), IsNotBanned(), IsRoomCreator()]
        return super().get_permissions()


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def list(self, request):
        logger.info("Listing all active rooms")
        rooms = Room.objects(is_active=True).order_by("-created_at")
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        logger.info(f"Retrieving room with id: {pk}")
        room = Room.objects(id=pk).first()
        if not room:
            logger.warning(f"Room not found with id: {pk}")
            return Response(
                {"detail": "اتاق پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(RoomSerializer(room).data)

    def create(self, request):
        logger.info("Creating new room")
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            room = Room(**serializer.validated_data)
            room.created_at = datetime.utcnow()
            room.creator = request.mongo_user
            room.save()
            logger.info(f"Room created successfully with id: {room.id}")
            return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)
        logger.error(f"Room creation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        logger.info(f"Attempting to delete room with id: {pk}")
        room = Room.objects(id=pk).first()
        if not room:
            logger.warning(f"Room not found for deletion with id: {pk}")
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, room)  # بررسی مالکیت
        room.delete()
        logger.info(f"Room deleted successfully with id: {pk}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action in ["destroy"]:
            return [IsAuthenticatedMongo(), IsNotBanned(), IsRoomCreator()]
        return super().get_permissions()


class ChallengeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def list(self, request):
        logger.info("Listing all challenges")
        challenges = Challenge.objects()
        serializer = ChallengeSerializer(challenges, many=True)
        return Response(serializer.data)

    def create(self, request):
        logger.info("Creating new challenge")
        serializer = ChallengeSerializer(data=request.data)
        if serializer.is_valid():
            challenge = Challenge(**serializer.validated_data)
            challenge.created_at = datetime.utcnow()
            challenge.save()
            logger.info(f"Challenge created successfully with id: {challenge.id}")
            return Response(
                ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED
            )
        logger.error(f"Challenge creation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def list(self, request):
        logger.info("Listing all messages")
        messages = Message.objects()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def create(self, request):
        logger.info("Creating new message")
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            message = Message(**serializer.validated_data)
            message.user_id = str(request.mongo_user.id)
            message.save()
            logger.info(f"Message created successfully with id: {message.id}")
            return Response(
                MessageSerializer(message).data, status=status.HTTP_201_CREATED
            )
        logger.error(f"Message creation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        logger.info(f"Attempting to like message with id: {pk}")
        message = Message.objects(id=pk).first()

        if not message:
            return Response(
                {"detail": "پیام پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
            )

        user_id = str(request.mongo_user.id)

        # بهتر است از atomic operation استفاده کنید
        if user_id not in (message.likes or []):
            Message.objects(id=pk).update_one(add_to_set__likes=user_id)
            message.reload()  # reload از MongoDB
            logger.info(f"Message liked successfully with id: {pk}")
        else:
            logger.info(f"Message already liked by user: {user_id}")

        return Response(MessageSerializer(message).data)

    @action(detail=True, methods=["delete"])
    def unlike(self, request, pk=None):
        logger.info(f"Attempting to unlike message with id: {pk}")
        message = Message.objects(id=pk).first()

        if not message:
            return Response(
                {"detail": "پیام پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
            )

        user_id = str(request.mongo_user.id)
        if user_id in (message.likes or []):
            Message.objects(id=pk).update_one(pull__likes=user_id)
            message.reload()
            logger.info(f"Message unliked successfully with id: {pk}")

        return Response(MessageSerializer(message).data)

    @action(detail=True, methods=["post"])
    def report(self, request, pk=None):
        logger.info(f"Attempting to report message with id: {pk}")
        message = Message.objects(id=pk).first()
        if message:
            message.is_reported = True
            message.save()
            logger.info(f"Message reported successfully with id: {pk}")
        else:
            logger.warning(f"Message report failed - message not found with id: {pk}")
        return Response({"reported": True})


class ChallengeResponseViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def create(self, request):
        logger.info("Creating challenge response")
        serializer = ChallengeResponseSerializer(data=request.data)
        if serializer.is_valid():
            try:
                response = ChallengeResponse(**serializer.validated_data)
                response.answered_at = datetime.utcnow()
                response.user = request.mongo_user
                response.save()
                logger.info(
                    f"Challenge response created successfully with id: {response.id}"
                )
                return Response(
                    ChallengeResponseSerializer(response).data,
                    status=status.HTTP_201_CREATED,
                )
            except NotUniqueError:
                logger.warning("Duplicate challenge response attempt")
                return Response(
                    {"error": "شما قبلاً پاسخ داده‌اید."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        logger.error(
            f"Challenge response creation failed with errors: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
