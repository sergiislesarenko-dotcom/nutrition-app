from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Goal(Base):
    """SQLAlchemy ORM model for the goals table."""

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    userId: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goalType: Mapped[str] = mapped_column("goal_type", String(30), nullable=False)
    targetWeightKg: Mapped[float | None] = mapped_column(
        "target_weight_kg", Float, nullable=True
    )
    dailyCaloriesKcal: Mapped[int | None] = mapped_column(
        "daily_calories_kcal", Integer, nullable=True
    )
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    isActive: Mapped[bool] = mapped_column(
        "is_active", Boolean, default=True, nullable=False
    )
