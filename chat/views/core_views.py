import logging
from datetime import datetime, timezone

from chat.auth_backends import IsAuthenticatedMongo, IsNotBanned, IsRoomCreator
from chat.models import Challenge, ChallengeResponse, Content, Message, Room, UserMood
from chat.serializers import (
    ChallengeResponseSerializer,
    ChallengeSerializer,
    ContentSerializer,
    MessageSerializer,
    RoomSerializer,
    UserMoodSerializer,
)
from mongoengine.errors import NotUniqueError, ValidationError
from rest_framework import status, views, viewsets
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
        rooms = Room.objects(is_active=True).order_by("-created_at")
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        logger.info(f"Retrieving room with id: {pk}")
        try:
            room = Room.objects(id=pk).first()
            if not room:
                logger.warning(f"Room not found with id: {pk}")
                return Response(
                    {"detail": "اتاق پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
                )
            return Response(RoomSerializer(room).data)
        except ValidationError:
            logger.error(f"Invalid room ID format: {pk}")
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        logger.info("Creating new room")
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            try:
                room = Room(**serializer.validated_data)
                room.creator = request.mongo_user
                room.save()
                logger.info(f"Room created successfully with id: {room.id}")
                return Response(
                    RoomSerializer(room).data, status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                logger.error(f"Room validation error: {str(e)}")
                return Response(
                    {"error": "خطا در اعتبارسنجی داده‌ها"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        logger.error(f"Room creation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        logger.info(f"Updating room with id: {pk}")
        try:
            room = Room.objects(id=pk).first()
            if not room:
                logger.warning(f"Room not found for update with id: {pk}")
                return Response(status=status.HTTP_404_NOT_FOUND)

            # بررسی مالکیت
            if room.creator != request.mongo_user:
                return Response(
                    {"detail": "شما مجاز به ویرایش این اتاق نیستید."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = RoomSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                for key, value in serializer.validated_data.items():
                    setattr(room, key, value)
                room.save()
                logger.info(f"Room updated successfully with id: {pk}")
                return Response(RoomSerializer(room).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        logger.info(f"Attempting to delete room with id: {pk}")
        try:
            room = Room.objects(id=pk).first()
            if not room:
                logger.warning(f"Room not found for deletion with id: {pk}")
                return Response(status=status.HTTP_404_NOT_FOUND)

            # بررسی مالکیت
            if room.creator != request.mongo_user:
                return Response(
                    {"detail": "شما مجاز به حذف این اتاق نیستید."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            room.delete()
            logger.info(f"Room deleted successfully with id: {pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError:
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )

    def get_permissions(self):
        if self.action in ["destroy", "update"]:
            return [IsAuthenticatedMongo(), IsNotBanned(), IsRoomCreator()]
        return super().get_permissions()


class ChallengeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def list(self, request):
        logger.info("Listing all challenges")
        room_id = request.query_params.get("room_id")
        if room_id:
            challenges = Challenge.objects(room=room_id).order_by("-created_at")
        else:
            challenges = Challenge.objects().order_by("-created_at")
        serializer = ChallengeSerializer(challenges, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        logger.info(f"Retrieving challenge with id: {pk}")
        try:
            challenge = Challenge.objects(id=pk).first()
            if not challenge:
                return Response(
                    {"detail": "چالش پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
                )
            return Response(ChallengeSerializer(challenge).data)
        except ValidationError:
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request):
        logger.info("Creating new challenge")
        serializer = ChallengeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                challenge = Challenge(**serializer.validated_data)
                challenge.save()
                logger.info(f"Challenge created successfully with id: {challenge.id}")
                return Response(
                    ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                logger.error(f"Challenge validation error: {str(e)}")
                return Response(
                    {"error": "خطا در اعتبارسنجی داده‌ها"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        logger.error(f"Challenge creation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def list(self, request):
        logger.info("Listing messages")
        challenge_id = request.query_params.get("challenge_id")
        if challenge_id:
            messages = Message.objects(
                challenge=challenge_id, is_deleted=False
            ).order_by("-created_at")
        else:
            messages = Message.objects(is_deleted=False).order_by("-created_at")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def create(self, request):
        logger.info("Creating new message")
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            try:
                message = Message(**serializer.validated_data)
                message.user_id = str(request.mongo_user.id)
                message.save()
                logger.info(f"Message created successfully with id: {message.id}")
                return Response(
                    MessageSerializer(message).data, status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                logger.error(f"Message validation error: {str(e)}")
                return Response(
                    {"error": "خطا در اعتبارسنجی داده‌ها"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        logger.error(f"Message creation failed with errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        logger.info(f"Attempting to delete message with id: {pk}")
        try:
            message = Message.objects(id=pk).first()
            if not message:
                return Response(status=status.HTTP_404_NOT_FOUND)

            # فقط صاحب پیام یا ادمین می‌تواند حذف کند
            if (
                message.user_id != str(request.mongo_user.id)
                and not request.mongo_user.is_admin
            ):
                return Response(
                    {"detail": "شما مجاز به حذف این پیام نیستید."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            message.is_deleted = True
            message.save()
            logger.info(f"Message soft deleted successfully with id: {pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError:
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        logger.info(f"Attempting to like message with id: {pk}")
        try:
            message = Message.objects(id=pk).first()
            if not message:
                return Response(
                    {"detail": "پیام پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
                )

            user_id = str(request.mongo_user.id)
            if user_id not in (message.likes or []):
                Message.objects(id=pk).update_one(add_to_set__likes=user_id)
                message.reload()
                logger.info(f"Message liked successfully with id: {pk}")
            else:
                logger.info(f"Message already liked by user: {user_id}")

            return Response(MessageSerializer(message).data)
        except ValidationError:
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["delete"])
    def unlike(self, request, pk=None):
        logger.info(f"Attempting to unlike message with id: {pk}")
        try:
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
        except ValidationError:
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def report(self, request, pk=None):
        logger.info(f"Attempting to report message with id: {pk}")
        try:
            message = Message.objects(id=pk).first()
            if not message:
                return Response(
                    {"detail": "پیام پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
                )

            message.is_reported = True
            message.save()
            logger.info(f"Message reported successfully with id: {pk}")
            return Response({"reported": True})
        except ValidationError:
            return Response(
                {"detail": "شناسه نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )


class ChallengeResponseViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedMongo, IsNotBanned]

    def list(self, request):
        logger.info("Listing challenge responses")
        responses = ChallengeResponse.objects(
            user_id=str(request.mongo_user.id)
        ).order_by("-answered_at")
        serializer = ChallengeResponseSerializer(responses, many=True)
        return Response(serializer.data)

    def create(self, request):
        logger.info("Creating challenge response")
        serializer = ChallengeResponseSerializer(data=request.data)
        if serializer.is_valid():
            try:
                response = ChallengeResponse(**serializer.validated_data)
                response.user_id = str(request.mongo_user.id)  # اصلاح شده
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
            except ValidationError as e:
                logger.error(f"Challenge response validation error: {str(e)}")
                return Response(
                    {"error": "خطا در اعتبارسنجی داده‌ها"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        logger.error(
            f"Challenge response creation failed with errors: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmitMoodAPIView(views.APIView):
    permission_classes = [IsAuthenticatedMongo]

    def post(self, request):
        logger.info("Submitting user mood")
        serializer = UserMoodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            UserMood.objects.create(
                user=request.mongo_user, mood=serializer.validated_data["mood"]
            )
            logger.info("User mood submitted successfully")
            return Response(
                {"message": "حال روحی ثبت شد."}, status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            logger.error(f"Mood validation error: {str(e)}")
            return Response(
                {"error": "خطا در ثبت حال روحی"}, status=status.HTTP_400_BAD_REQUEST
            )


class MoodSuggestionsAPIView(views.APIView):
    permission_classes = [IsAuthenticatedMongo]

    def get(self, request):
        logger.info("Getting mood suggestions")
        last_mood = (
            UserMood.objects(user=request.mongo_user).order_by("-created_at").first()
        )
        if not last_mood:
            return Response({"suggestions": []}, status=status.HTTP_200_OK)

        contents = Content.objects(mood_tags=last_mood.mood).order_by("-created_at")[
            :20
        ]
        serializer = ContentSerializer(contents, many=True)
        return Response({"suggestions": serializer.data}, status=status.HTTP_200_OK)


class PopularContentAPIView(views.APIView):
    def get(self, request):
        logger.info("Getting popular content")
        contents = Content.objects(is_popular=True).order_by("-created_at")[:10]
        serializer = ContentSerializer(contents, many=True)
        return Response({"popular": serializer.data}, status=status.HTTP_200_OK)


class CategoryListAPIView(views.APIView):
    def get(self, request):
        logger.info("Getting content categories")
        categories = Content.objects.distinct("category")
        return Response({"categories": categories}, status=status.HTTP_200_OK)
