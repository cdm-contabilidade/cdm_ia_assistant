from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import ProviderCredential

ProviderName = Literal['gemini', 'openai']


class ProviderCredentialError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 503):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class ProviderKeyStatus:
    provider: ProviderName
    configured: bool
    source: Literal['database', 'environment', 'none']
    last4: str | None
    updated_at: datetime | None
    disabled: bool = False

    @property
    def masked_last4(self) -> str | None:
        return f'****{self.last4}' if self.last4 else None


def _environment_key(provider: ProviderName) -> str | None:
    settings = get_settings()
    value = settings.google_api_key if provider == 'gemini' else settings.openai_api_key
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _fernet() -> Fernet:
    key = get_settings().provider_keys_encryption_key
    if not isinstance(key, str) or not key.strip():
        raise ProviderCredentialError(
            'provider_key_encryption_unavailable',
            'A chave mestre de criptografia dos provedores não está configurada.',
        )
    try:
        return Fernet(key.strip().encode('ascii'))
    except (ValueError, UnicodeEncodeError, TypeError) as exc:
        raise ProviderCredentialError(
            'provider_key_encryption_unavailable',
            'A chave mestre de criptografia dos provedores é inválida.',
        ) from exc


def encrypt_provider_key(api_key: str) -> str:
    value = api_key.strip()
    if not value:
        raise ProviderCredentialError('provider_key_invalid', 'A chave da API não pode ficar vazia.', status_code=422)
    return _fernet().encrypt(value.encode('utf-8')).decode('ascii')


def decrypt_provider_key(encrypted_api_key: str) -> str:
    try:
        return _fernet().decrypt(encrypted_api_key.encode('ascii')).decode('utf-8')
    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise ProviderCredentialError(
            'provider_key_unavailable',
            'A credencial armazenada do provedor não pode ser descriptografada.',
        ) from exc


async def resolve_provider_api_key(db: AsyncSession, provider: ProviderName) -> str | None:
    credential = await db.get(ProviderCredential, provider)
    if credential is not None:
        if credential.disabled:
            return None
        if not credential.encrypted_api_key:
            raise ProviderCredentialError(
                'provider_key_unavailable',
                'A credencial armazenada do provedor não está disponível.',
            )
        return decrypt_provider_key(credential.encrypted_api_key)
    return _environment_key(provider)


async def require_provider_api_key(db: AsyncSession, provider: ProviderName) -> str:
    api_key = await resolve_provider_api_key(db, provider)
    if api_key is None:
        label = 'Google Gemini' if provider == 'gemini' else 'OpenAI'
        raise ProviderCredentialError(
            'provider_not_configured',
            f'O provedor {label} não está configurado. Cadastre uma chave ou configure a variável de ambiente compatível.',
        )
    return api_key


async def provider_key_status(db: AsyncSession, provider: ProviderName) -> ProviderKeyStatus:
    credential = await db.get(ProviderCredential, provider)
    if credential is not None:
        return ProviderKeyStatus(provider, not credential.disabled, 'database', credential.last4, credential.updated_at, credential.disabled)
    environment_key = _environment_key(provider)
    if environment_key is not None:
        return ProviderKeyStatus(provider, True, 'environment', environment_key[-4:], None)
    return ProviderKeyStatus(provider, False, 'none', None, None)


async def store_provider_api_key(db: AsyncSession, provider: ProviderName, api_key: str) -> ProviderCredential:
    value = api_key.strip()
    encrypted = encrypt_provider_key(value)
    credential = await db.get(ProviderCredential, provider)
    if credential is None:
        credential = ProviderCredential(provider=provider, encrypted_api_key=encrypted, last4=value[-4:])
        db.add(credential)
    else:
        credential.encrypted_api_key = encrypted
        credential.last4 = value[-4:]
        credential.disabled = False
    return credential


async def disable_provider_api_key(db: AsyncSession, provider: ProviderName) -> ProviderCredential:
    credential = await db.get(ProviderCredential, provider)
    if credential is None:
        credential = ProviderCredential(provider=provider, encrypted_api_key=None, last4=None, disabled=True)
        db.add(credential)
    else:
        credential.encrypted_api_key = None
        credential.last4 = None
        credential.disabled = True
    return credential


async def revert_provider_to_environment(db: AsyncSession, provider: ProviderName) -> None:
    credential = await db.get(ProviderCredential, provider)
    if credential is not None:
        await db.delete(credential)


def environment_provider_api_key(provider: ProviderName) -> str | None:
    return _environment_key(provider)
