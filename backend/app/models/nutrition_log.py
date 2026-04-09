from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NutritionLog(Base):
    """SQLAlchemy ORM model for the nutrition_logs table."""

    __tablename__ = "nutrition_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    userId: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    loggedAt: Mapped[datetime] = mapped_column(
        "logged_at", DateTime, server_default=func.now(), nullable=False
    )
    mealType: Mapped[str] = mapped_column("meal_type", String(20), nullable=False)
    foodName: Mapped[str] = mapped_column("food_name", String(255), nullable=False)
    weightG: Mapped[float] = mapped_column("weight_g", Float, nullable=False)
    caloriesKcal: Mapped[float] = mapped_column("calories_kcal", Float, nullable=False)
    proteinG: Mapped[float] = mapped_column("protein_g", Float, nullable=False)
    carbsG: Mapped[float] = mapped_column("carbs_g", Float, nullable=False)
    fatG: Mapped[float] = mapped_column("fat_g", Float, nullable=False)
