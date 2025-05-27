import datetime

from rest_framework import serializers

from .models import Challenge, ChallengeResponse, Message, Room, User


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_username(self, value):
        if not value:
            raise serializers.ValidationError("نام کاربری نمی‌تواند خالی باشد.")
        return value

    def validate_email(self, value):
        if value and "@" not in value:
            raise serializers.ValidationError("ایمیل وارد شده معتبر نیست.")
        return value


class RoomSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True)
    room_type = serializers.ChoiceField(choices=[x[0] for x in Room.ROOM_TYPES])
    language = serializers.CharField(default="fa")
    max_members = serializers.IntegerField(default=100)
    creator = serializers.CharField()
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تنظیم queryset بعد از اطمینان از اتصال به DB
        try:
            self.fields["creator"].queryset = User.objects.all()
        except Exception:
            self.fields["creator"].queryset = User.objects.none()

    def validate_title(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("عنوان نمی‌تواند خالی باشد.")
        return value

    def validate_max_members(self, value):
        if value <= 0:
            raise serializers.ValidationError("حداکثر اعضا باید بزرگ‌تر از صفر باشد.")
        return value

    def validate_language(self, value):
        if not value:
            return "fa"
        return value

    def validate_creator(self, value):
        from .models import User

        if not User.objects(id=value).first():
            raise serializers.ValidationError("کاربر پیدا نشد.")
        return value


class ChallengeSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    room = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True)
    media_url = serializers.URLField(required=False, allow_null=True)
    expiration_time = serializers.DateTimeField()
    created_at = serializers.DateTimeField(read_only=True)

    def validate_room(self, value):
        if not Room.objects.filter(id=value).exists():
            raise serializers.ValidationError("اتاق وجود ندارد.")
        return value

    def validate_title(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("عنوان نمی‌تواند خالی باشد.")
        return value

    def validate_expiration_time(self, value):
        if value <= datetime.datetime.utcnow():
            raise serializers.ValidationError("زمان انقضا باید در آینده باشد.")
        return value


class MessageSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    challenge = serializers.CharField(required=False, allow_null=True)
    user_id = serializers.CharField(read_only=True)
    content = serializers.CharField()
    is_reply = serializers.BooleanField(default=False)
    parent_message = serializers.CharField(allow_null=True, required=False)
    is_rebuke = serializers.BooleanField(default=False)
    is_back = serializers.BooleanField(default=False)
    is_edited = serializers.BooleanField(default=False)
    is_reported = serializers.BooleanField(default=False)
    is_deleted = serializers.BooleanField(default=False)
    likes = serializers.ListField(child=serializers.CharField(), required=False)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_content(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("متن پیام نمی‌تواند خالی باشد.")
        return value


class ChallengeResponseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    challenge = serializers.CharField()
    answered_at = serializers.DateTimeField(read_only=True)

    def validate_challenge(self, value):
        if not Challenge.objects.filter(id=value).exists():
            raise serializers.ValidationError("چالش وجود ندارد.")
        return value
