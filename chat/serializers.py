from datetime import datetime, timezone

from rest_framework import serializers

from .models import Challenge, ChallengeResponse, Content, Message, Room, User


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField(max_length=100)
    phone = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=False, allow_null=True)
    is_banned = serializers.BooleanField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_username(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("نام کاربری نمی‌تواند خالی باشد.")
        return value.strip()

    def validate_email(self, value):
        if value and "@" not in value:
            raise serializers.ValidationError("ایمیل وارد شده معتبر نیست.")
        return value


class RoomSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=100)
    description = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    room_type = serializers.ChoiceField(choices=[x[0] for x in Room.ROOM_TYPES])
    language = serializers.CharField(default="fa", max_length=10)
    max_members = serializers.IntegerField(default=100, min_value=1, max_value=1000)
    creator = UserSerializer(read_only=True)  # نمایش اطلاعات creator
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("عنوان نمی‌تواند خالی باشد.")
        return value.strip()

    def validate_max_members(self, value):
        if value <= 0:
            raise serializers.ValidationError("حداکثر اعضا باید بزرگ‌تر از صفر باشد.")
        if value > 1000:
            raise serializers.ValidationError(
                "حداکثر اعضا نمی‌تواند بیش از ۱۰۰۰ نفر باشد."
            )
        return value

    def validate_language(self, value):
        if not value:
            return "fa"
        return value.strip().lower()

    def to_representation(self, instance):
        """Custom representation for Room objects"""
        data = super().to_representation(instance)
        if hasattr(instance, "creator") and instance.creator:
            data["creator"] = UserSerializer(instance.creator).data
        return data


class ChallengeSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    room = serializers.CharField()
    title = serializers.CharField(max_length=100)
    description = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    media_url = serializers.URLField(required=False, allow_null=True)
    expiration_time = serializers.DateTimeField()
    created_at = serializers.DateTimeField(read_only=True)

    def validate_room(self, value):
        """Validate room exists"""
        try:
            room = Room.objects(id=value).first()
            if not room:
                raise serializers.ValidationError("اتاق وجود ندارد.")
            if not room.is_active:
                raise serializers.ValidationError("این اتاق غیرفعال است.")
            return value
        except Exception:
            raise serializers.ValidationError("شناسه اتاق نامعتبر است.")

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("عنوان نمی‌تواند خالی باشد.")
        return value.strip()

    def validate_expiration_time(self, value):
        # اطمینان از timezone-aware comparison
        now = datetime.now(timezone.utc)
        if value <= now:
            raise serializers.ValidationError("زمان انقضا باید در آینده باشد.")
        return value

    def to_representation(self, instance):
        """Custom representation for Challenge objects"""
        data = super().to_representation(instance)
        if hasattr(instance, "room") and instance.room:
            data["room"] = {
                "id": str(instance.room.id),
                "title": instance.room.title,
                "room_type": instance.room.room_type,
            }
        return data


class MessageSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    challenge = serializers.CharField(required=False, allow_null=True)
    user_id = serializers.CharField(read_only=True)
    content = serializers.CharField(max_length=1000)
    is_reply = serializers.BooleanField(default=False)
    parent_message = serializers.CharField(allow_null=True, required=False)
    is_rebuke = serializers.BooleanField(default=False)
    is_back = serializers.BooleanField(default=False)
    is_edited = serializers.BooleanField(read_only=True)
    is_reported = serializers.BooleanField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    likes = serializers.ListField(child=serializers.CharField(), read_only=True)
    likes_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_likes_count(self, obj):
        """Return count of likes"""
        return len(obj.likes) if obj.likes else 0

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("متن پیام نمی‌تواند خالی باشد.")

        # بررسی طول پیام
        if len(value.strip()) > 1000:
            raise serializers.ValidationError("پیام نمی‌تواند بیش از ۱۰۰۰ کاراکتر باشد.")

        return value.strip()

    def validate_challenge(self, value):
        """Validate challenge exists if provided"""
        if value:
            try:
                challenge = Challenge.objects(id=value).first()
                if not challenge:
                    raise serializers.ValidationError("چالش وجود ندارد.")
                return value
            except Exception:
                raise serializers.ValidationError("شناسه چالش نامعتبر است.")
        return value

    def validate_parent_message(self, value):
        """Validate parent message exists if this is a reply"""
        if value:
            try:
                parent = Message.objects(id=value).first()
                if not parent:
                    raise serializers.ValidationError("پیام والد یافت نشد.")
                if parent.is_deleted:
                    raise serializers.ValidationError(
                        "نمی‌توان به پیام حذف شده پاسخ داد."
                    )
                return value
            except Exception:
                raise serializers.ValidationError("شناسه پیام والد نامعتبر است.")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        # اگر is_reply True است، parent_message باید وجود داشته باشد
        if attrs.get("is_reply") and not attrs.get("parent_message"):
            raise serializers.ValidationError(
                {"parent_message": "برای پیام پاسخ، پیام والد الزامی است."}
            )

        return attrs


class ChallengeResponseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    challenge = serializers.CharField()
    answered_at = serializers.DateTimeField(read_only=True)

    def validate_challenge(self, value):
        """Validate challenge exists and is not expired"""
        try:
            challenge = Challenge.objects(id=value).first()
            if not challenge:
                raise serializers.ValidationError("چالش وجود ندارد.")

            # بررسی انقضا
            now = datetime.now(timezone.utc)
            if challenge.expiration_time <= now:
                raise serializers.ValidationError("این چالش منقضی شده است.")

            return value
        except Exception:
            raise serializers.ValidationError("شناسه چالش نامعتبر است.")

    def to_representation(self, instance):
        """Custom representation for ChallengeResponse objects"""
        data = super().to_representation(instance)
        if hasattr(instance, "challenge") and instance.challenge:
            data["challenge"] = {
                "id": str(instance.challenge.id),
                "title": instance.challenge.title,
                "room": (
                    str(instance.challenge.room.id) if instance.challenge.room else None
                ),
            }
        return data


class ContentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    category = serializers.ChoiceField(
        choices=["meditation", "music", "story", "chatbot"]
    )
    media_url = serializers.URLField(required=False, allow_null=True)
    mood_tags = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["happy", "sad", "angry", "stressed", "relaxed", "neutral"]
        ),
        required=False,
        allow_empty=True,
    )
    is_popular = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("عنوان نمی‌تواند خالی باشد.")
        return value.strip()

    def validate_mood_tags(self, value):
        """Validate mood tags are valid choices"""
        valid_moods = ["happy", "sad", "angry", "stressed", "relaxed", "neutral"]
        if value:
            for mood in value:
                if mood not in valid_moods:
                    raise serializers.ValidationError(f"حالت '{mood}' معتبر نیست.")
        return value


class UserMoodSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user = serializers.CharField(read_only=True)
    mood = serializers.ChoiceField(
        choices=["happy", "sad", "angry", "stressed", "relaxed", "neutral"]
    )
    created_at = serializers.DateTimeField(read_only=True)

    def validate_mood(self, value):
        """Validate mood is a valid choice"""
        valid_moods = ["happy", "sad", "angry", "stressed", "relaxed", "neutral"]
        if value not in valid_moods:
            raise serializers.ValidationError("حالت روحی انتخاب شده معتبر نیست.")
        return value


# Serializer برای OTP (اگه نیازه)
class OTPCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6, min_length=4)

    def validate_phone(self, value):
        """Validate phone number format"""
        if not value.startswith("+") and not value.startswith("09"):
            raise serializers.ValidationError("شماره تلفن معتبر نیست.")
        return value

    def validate_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError("کد تأیید باید عددی باشد.")
        return value
