import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    duration: Mapped[int] = mapped_column(Integer)
    aspect_ratio: Mapped[str] = mapped_column(String(10))
    model_used: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    resolution: Mapped[str] = mapped_column(String(20), default="1280x720")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="videos")  # noqa: F821
    job: Mapped["Job"] = relationship(back_populates="video")  # noqa: F821
