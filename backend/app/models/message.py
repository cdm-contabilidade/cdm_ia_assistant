import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, Text, Uuid, func
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
