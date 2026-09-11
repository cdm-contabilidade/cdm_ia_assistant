import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Uuid, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIModel(Base):
    __tablename__ = 'ai_models'
    __table_args__ = (
        CheckConstraint("provider IN ('gemini', 'openai')", name='ck_ai_models_provider'),
        UniqueConstraint('provider', 'model_id', name='uq_ai_models_provider_model_id'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[Literal['gemini', 'openai']] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
