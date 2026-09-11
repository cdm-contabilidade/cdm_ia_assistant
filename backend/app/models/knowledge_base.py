import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, Uuid, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KnowledgeBase(Base):
    __tablename__ = 'knowledge_bases'
    __table_args__ = (
        CheckConstraint("provider = 'gemini'", name='ck_knowledge_bases_provider'),
        CheckConstraint('NOT featured OR active', name='ck_knowledge_bases_featured_active'),
        UniqueConstraint('file_search_store_id', name='uq_knowledge_bases_file_search_store_id'),
        Index(
            'uq_knowledge_bases_featured',
            'featured',
            unique=True,
            postgresql_where=text('featured IS TRUE'),
            sqlite_where=text('featured = 1'),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[Literal['gemini']] = mapped_column(String(20), nullable=False, default='gemini', server_default='gemini')
    file_search_store_id: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true', nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
