import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Chat(Base):
    __tablename__ = 'chats'
    __table_args__ = (Index('ix_chats_user_id', 'user_id'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped['User'] = relationship(back_populates='chats')
    messages: Mapped[list['Message']] = relationship(back_populates='chat', cascade='all, delete-orphan', order_by='Message.created_at')
