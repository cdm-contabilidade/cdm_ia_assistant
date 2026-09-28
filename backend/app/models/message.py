import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, LargeBinary, PrimaryKeyConstraint, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name='ck_messages_role'),
        Index('ix_messages_chat_id', 'chat_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    has_image: Mapped[bool] = mapped_column(default=False, nullable=False)
    image_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    # Provider/model identifiers are safe operational metadata; credentials are
    # deliberately never accepted by the API or stored here.
    provider_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    chat: Mapped['Chat'] = relationship(back_populates='messages')
    # Never read `images` lazily in async code (MissingGreenlet); loads go through
    # explicit queries. ORM cascade keeps deletes working where PRAGMA foreign_keys is off.
    images: Mapped[list['MessageImage']] = relationship(back_populates='message', cascade='all, delete-orphan', order_by='MessageImage.position')


class MessageImage(Base):
    __tablename__ = 'message_images'
    __table_args__ = (
        PrimaryKeyConstraint('message_id', 'position', name='pk_message_images'),
        CheckConstraint('position BETWEEN 0 AND 3', name='ck_message_images_position'),
    )

    message_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    mime: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    message: Mapped['Message'] = relationship(back_populates='images')
