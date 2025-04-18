from sqlalchemy import Integer, String, Boolean, Float, ARRAY, Enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column
import enum

from src.core.database.alchemy_models.base import Base


class AccommodationPreference(str, enum.Enum):
    APARTMENT = "apartment"
    DORMITORY = "dormitory"
    NO_PREFERENCE = "no_preference"


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    user_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

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

    study_location: Mapped[str] = mapped_column(nullable=True)
    study_program: Mapped[str] = mapped_column(nullable=True)
    accommodation_preference: Mapped[str] = mapped_column(
        Enum(AccommodationPreference, native_enum=False),
        nullable=True
    )

    telegram_username: Mapped[str] = mapped_column(nullable=True)