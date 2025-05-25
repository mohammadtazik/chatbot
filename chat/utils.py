# chat/utils.py
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from passlib.context import CryptContext


def generate_tokens(user):
    now = datetime.now(timezone.utc)
    access_payload = {
        "phone": user.phone,
        "type": "access",
        "exp": now + timedelta(minutes=300),
        "iat": now,
    }
    refresh_payload = {
        "phone": user.phone,
        "type": "refresh",
        "exp": now + timedelta(days=30),
        "iat": now,
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")
    return access_token, refresh_token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
