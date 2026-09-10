from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from .config import get_settings

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


def create_token(subject: UUID, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {'sub': str(subject), 'type': token_type, 'iat': now, 'exp': now + lifetime, 'jti': str(uuid4())}
    return jwt.encode(payload, get_settings().jwt_secret_key, algorithm='HS256')


def create_access_token(subject: UUID) -> str:
    minutes = get_settings().access_token_expire_minutes
    return create_token(subject, 'access', timedelta(minutes=minutes))


def create_refresh_token(subject: UUID) -> str:
    days = get_settings().refresh_token_expire_days
    return create_token(subject, 'refresh', timedelta(days=days))


def decode_token(token: str, expected_type: str) -> UUID:
    payload = jwt.decode(token, get_settings().jwt_secret_key, algorithms=['HS256'])
    if payload.get('type') != expected_type or not payload.get('sub'):
        raise jwt.InvalidTokenError('invalid token type')
    return UUID(str(payload['sub']))
