from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.alchemy_models.base import Base


class User(Base):
    username: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
