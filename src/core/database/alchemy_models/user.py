from sqlalchemy import Integer, String, Boolean, Float, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.alchemy_models.base import Base


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    name: Mapped[str] = mapped_column(nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(nullable=True)
    occupation: Mapped[str] = mapped_column(nullable=True)
    avatar: Mapped[str] = mapped_column(nullable=True)
    bio: Mapped[str] = mapped_column(nullable=True)
    interests: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    cleanliness_level: Mapped[int] = mapped_column(Integer, nullable=True)
    sleep_habits: Mapped[str] = mapped_column(nullable=True)
    rent_budget: Mapped[int] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(nullable=True)
    smoking_preference: Mapped[str] = mapped_column(nullable=True)
    pet_preference: Mapped[str] = mapped_column(nullable=True)