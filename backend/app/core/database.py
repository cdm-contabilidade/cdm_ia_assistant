from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings

class Base(DeclarativeBase):
    pass


@lru_cache
def get_ssh_tunnel():
    settings = get_settings()
    if not settings.ssh_enable:
        return None
    from sshtunnel import SSHTunnelForwarder

    tunnel = SSHTunnelForwarder(
        (settings.ssh_host, settings.ssh_port),
        ssh_username=settings.ssh_user,
        ssh_password=settings.ssh_password or None,
        ssh_pkey=settings.ssh_private_key or None,
        remote_bind_address=(settings.db_host, settings.db_port),
        local_bind_address=('127.0.0.1', 0),
    )
    tunnel.start()
    return tunnel


def get_database_url() -> str:
    settings = get_settings()
    tunnel = get_ssh_tunnel()
    return settings.database_dsn(port=tunnel.local_bind_port if tunnel else None)


@lru_cache
def get_engine():
    return create_async_engine(get_database_url(), pool_pre_ping=True)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session
