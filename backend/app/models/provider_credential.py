from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProviderCredential(Base):
    """Encrypted provider credential; the provider key is the logical primary key."""

    __tablename__ = 'provider_credentials'
    __table_args__ = (
        CheckConstraint("provider IN ('gemini', 'openai')", name='ck_provider_credentials_provider'),
    )

    provider: Mapped[Literal['gemini', 'openai']] = mapped_column(String(20), primary_key=True)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
