from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import get_engine, get_session_factory
from app.core.security import hash_password
from app.models import User

DEFAULT_EMAIL = 'admin@cdmcontabilidade.com.br'
DEFAULT_NAME = 'admin'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Cria ou atualiza o administrador inicial de forma idempotente.')
    parser.add_argument('--email', default=os.getenv('ADMIN_EMAIL', DEFAULT_EMAIL))
    parser.add_argument('--name', default=os.getenv('ADMIN_NAME', DEFAULT_NAME))
    parser.add_argument('--password', default=os.getenv('ADMIN_PASSWORD'))
    return parser.parse_args()


async def seed(email: str, name: str, password: str) -> None:
    async with get_session_factory()() as db:
        user = await db.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None:
            user = User(email=email.strip().lower(), name=name.strip() or DEFAULT_NAME, password_hash=hash_password(password))
            db.add(user)
        else:
            user.name = name.strip() or DEFAULT_NAME
            user.password_hash = hash_password(password)
        user.role = 'admin'
        user.is_active = True
        user.is_blacklisted = False
        await db.commit()
        print(f'Administrador pronto: {user.email}')
    await get_engine().dispose()


def main() -> int:
    args = parse_args()
    if not args.password or len(args.password) < 8:
        print('Informe ADMIN_PASSWORD ou --password com pelo menos 8 caracteres.', file=sys.stderr)
        return 2
    asyncio.run(seed(args.email, args.name, args.password))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
