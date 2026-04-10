from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Food(Base):
    """SQLAlchemy ORM model for the global foods reference table."""

    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    caloriesPer100g: Mapped[float] = mapped_column(
        "calories_per_100g", Float, nullable=False
    )
    proteinPer100g: Mapped[float] = mapped_column(
        "protein_per_100g", Float, nullable=False
    )
    carbsPer100g: Mapped[float] = mapped_column(
        "carbs_per_100g", Float, nullable=False
    )
    fatPer100g: Mapped[float] = mapped_column(
        "fat_per_100g", Float, nullable=False
    )
