import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Literal['admin', 'collaborator']] = mapped_column(String(20), default='collaborator', server_default='collaborator', nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true', nullable=False)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chats: Mapped[list['Chat']] = relationship(back_populates='user', cascade='all, delete-orphan')
