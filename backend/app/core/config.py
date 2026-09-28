from functools import lru_cache
from pathlib import Path
import sys
from urllib.parse import quote

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def packaged_env_file() -> Path:
    executable_root = Path(sys.executable).resolve().parent
    candidates = (
        executable_root / 'backend' / '.env',
        executable_root.parent / 'backend' / '.env',
    )
    return next((candidate for candidate in candidates if candidate.is_file()), candidates[0])


if getattr(sys, 'frozen', False):
    ENV_FILE = packaged_env_file()
else:
    ENV_FILE = Path(__file__).resolve().parents[2] / '.env'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding='utf-8', case_sensitive=False, extra='ignore')

    database_url: str | None = None
    db_host: str = '127.0.0.1'
    db_port: int = 5432
    db_name: str = 'ia_assistant'
    db_user: str = 'user_ia'
    db_password: str = ''
    ssh_enable: bool = False
    ssh_host: str | None = None
    ssh_port: int = 22
    ssh_user: str | None = None
    ssh_password: str | None = None
    ssh_private_key: str | None = None
    jwt_secret_key: str = Field(min_length=32)
    google_api_key: str | None = None
    google_file_search_store_name: str = Field(min_length=1)
    google_gemini_model: str | None = None
    openai_api_key: str | None = None
    provider_keys_encryption_key: str | None = None
    openai_timeout_seconds: float = 90
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    google_timeout_seconds: float = 90
    image_max_bytes: int = 5_242_880
    frontend_origins: str = 'http://localhost:5173'
    cookie_secure: bool = False
    app_env: str = 'development'
    rate_limit_window_seconds: int = 60
    rate_limit_max_attempts: int = 30
    max_request_bytes: int = 12_000_000

    @model_validator(mode='after')
    def validate_runtime(self):
        if self.google_api_key is not None and not self.google_api_key.strip():
            self.google_api_key = None
        if not self.google_file_search_store_name.strip():
            raise ValueError('GOOGLE_FILE_SEARCH_STORE_NAME is required.')
        if self.ssh_enable and (not self.ssh_host or not self.ssh_user or (not self.ssh_password and not self.ssh_private_key)):
            raise ValueError('SSH_HOST, SSH_USER and SSH_PASSWORD or SSH_PRIVATE_KEY are required when SSH_ENABLE=true.')
        if not self.database_url and not all((self.db_host, self.db_name, self.db_user, self.db_password)):
            raise ValueError('DATABASE_URL or DB_HOST, DB_NAME, DB_USER and DB_PASSWORD are required.')
        if self.app_env.lower() not in {'test', 'testing'} and self.database_url and self.database_url.startswith('sqlite'):
            raise ValueError('DATABASE_URL must use PostgreSQL outside tests.')
        return self

    def database_dsn(self, host: str | None = None, port: int | None = None) -> str:
        # A SQLite URL is only allowed in tests (see validate_runtime) and must never
        # be redirected through the SSH tunnel.
        if self.database_url and (not self.ssh_enable or self.database_url.startswith('sqlite')):
            return self.database_url
        target_host = host or self.db_host
        target_port = port or self.db_port
        user = quote(self.db_user, safe='')
        password = quote(self.db_password, safe='')
        name = quote(self.db_name, safe='')
        return f'postgresql+asyncpg://{user}:{password}@{target_host}:{target_port}/{name}'

    @property
    def frontend_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
