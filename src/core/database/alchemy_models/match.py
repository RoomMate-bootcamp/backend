from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.alchemy_models.base import Base


class Match(Base):
    user1_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user2_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user1 = relationship("User", foreign_keys=[user1_id], backref="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], backref="matches_as_user2")
