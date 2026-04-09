from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Restriction(Base):
    """SQLAlchemy ORM model for the restrictions table."""

    __tablename__ = "restrictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    userId: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
