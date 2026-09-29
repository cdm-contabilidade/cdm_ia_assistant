from datetime import datetime, timedelta, timezone
from typing import Any
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
    payload = {'sub': str(subject), 'type': token_type, 'iat': now.timestamp(), 'exp': (now + lifetime).timestamp(), 'jti': str(uuid4())}
    return jwt.encode(payload, get_settings().jwt_secret_key, algorithm='HS256')


def create_access_token(subject: UUID) -> str:
    minutes = get_settings().access_token_expire_minutes
    return create_token(subject, 'access', timedelta(minutes=minutes))


def create_refresh_token(subject: UUID) -> str:
    days = get_settings().refresh_token_expire_days
    return create_token(subject, 'refresh', timedelta(days=days))


def decode_token_claims(token: str, expected_type: str) -> dict[str, Any]:
    payload = jwt.decode(token, get_settings().jwt_secret_key, algorithms=['HS256'])
    if payload.get('type') != expected_type or not payload.get('sub'):
        raise jwt.InvalidTokenError('invalid token type')
    return payload


def token_predates_password_change(claims: dict[str, Any], password_changed_at: datetime | None) -> bool:
    if password_changed_at is None:
        return False
    changed_at = password_changed_at
    if changed_at.tzinfo is None:
        changed_at = changed_at.replace(tzinfo=timezone.utc)
    issued_at = claims.get('iat')
    return issued_at is None or datetime.fromtimestamp(float(issued_at), timezone.utc) < changed_at


def decode_token(token: str, expected_type: str) -> UUID:
    return UUID(str(decode_token_claims(token, expected_type)['sub']))
