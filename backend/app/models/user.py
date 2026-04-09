from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """SQLAlchemy ORM model for the users table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    passwordHash: Mapped[str] = mapped_column(
        "password_hash", String(255), nullable=False
    )
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weightKg: Mapped[float | None] = mapped_column("weight_kg", Float, nullable=True)
    heightCm: Mapped[float | None] = mapped_column("height_cm", Float, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activityLevel: Mapped[str | None] = mapped_column(
        "activity_level", String(20), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
