from datetime import datetime, timezone

from mongoengine import BooleanField, DateTimeField, Document, StringField, fields
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Document):
    username = fields.StringField(required=True, unique=False)
    phone = fields.StringField(required=True, unique=True)
    password = fields.StringField(required=False)
    email = fields.EmailField()
    is_banned = fields.BooleanField(default=False)
    is_admin = BooleanField(default=False)
    created_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {"collection": "users", "indexes": ["phone"]}

    def set_password(self, raw_password):
        self.password = pwd_context.hash(raw_password)

    def check_password(self, raw_password):
        if not self.password:
            return False
        return pwd_context.verify(raw_password, self.password)


class Room(Document):
    ROOM_TYPES = (
        ("daily", "چالش روزانه"),
        ("teens", "نوجوانان"),
        ("mothers", "مادران"),
    )

    title = fields.StringField(required=True, max_length=100)
    description = fields.StringField()
    room_type = fields.StringField(choices=ROOM_TYPES)
    language = fields.StringField(default="fa")
    max_members = fields.IntField(default=100)
    created_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))
    creator = fields.ReferenceField(User)
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "rooms",
        "indexes": [
            "room_type",
            "creator",
            {"fields": ["-created_at"], "sparse": True},
        ],
    }


class Challenge(Document):
    room = fields.ReferenceField(Room, reverse_delete_rule=2)  # CASCADE
    title = fields.StringField(required=True, max_length=100)
    description = fields.StringField()
    media_url = fields.URLField()
    created_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))
    expiration_time = fields.DateTimeField(required=True)

    meta = {
        "collection": "challenges",
        "indexes": ["room", {"fields": ["expiration_time"], "expireAfterSeconds": 0}],
    }


class Message(Document):
    challenge = fields.ReferenceField(
        Challenge, reverse_delete_rule=2, required=False
    )  # CASCADE
    user_id = fields.StringField(required=True)  # ناشناس
    content = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))
    is_reply = fields.BooleanField(default=False)
    parent_message = fields.ReferenceField("self")
    is_rebuke = fields.BooleanField(default=False)  # ریبای (توبیخ)
    is_back = fields.BooleanField(default=False)  # البک
    is_edited = fields.BooleanField(default=False)
    is_reported = fields.BooleanField(default=False)
    is_deleted = fields.BooleanField(default=False)
    likes = fields.ListField(fields.StringField())  # شناسه کاربران لایک‌کننده

    meta = {
        "collection": "messages",
        "indexes": [
            "challenge",
            "user_id",
            {"fields": ["-created_at"], "sparse": True},
        ],
    }


class ChallengeResponse(Document):
    user_id = fields.StringField(required=True)
    challenge = fields.ReferenceField(Challenge)
    answered_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "challenge_responses",
        "indexes": [{"fields": ["user_id", "challenge"], "unique": True}],
    }


class OTPCode(Document):
    phone = StringField(required=True)
    code = StringField(required=True)
    expires_at = DateTimeField(required=True)

    meta = {
        "collection": "otp_codes",
        "indexes": [{"fields": ["expires_at"], "expireAfterSeconds": 0}, "phone"],
    }


class UserMood(Document):
    user = fields.ReferenceField(User, required=True)
    mood = fields.StringField(
        required=True,
        choices=["happy", "sad", "angry", "stressed", "relaxed", "neutral"],
    )
    created_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {"collection": "user_moods", "indexes": ["user", "-created_at"]}


class Content(Document):
    title = fields.StringField(required=True)
    description = fields.StringField()
    category = fields.StringField(
        required=True, choices=["meditation", "music", "story", "chatbot"]
    )
    mood_tags = fields.ListField(fields.StringField())  # مثل ["relaxed", "happy"]
    media_url = fields.URLField()
    is_popular = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "contents",
        "indexes": ["category", "mood_tags", "-created_at"],
    }
