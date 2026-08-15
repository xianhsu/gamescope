from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.constants import JobStatus


class ProcessingJob(Base):
    """One ingestion run for one source. Powers the /system page + observability."""

    __tablename__ = "processing_job"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("source.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default=JobStatus.PENDING, nullable=False)

    articles_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_stored: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
