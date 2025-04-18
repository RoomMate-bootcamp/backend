from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey, String, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.alchemy_models.base import Base


class LikeStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Like(Base):
    liker_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    liked_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[LikeStatus] = mapped_column(
        Enum(LikeStatus), default=LikeStatus.PENDING
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    liker = relationship("User", foreign_keys=[liker_id], backref="likes_given")
    liked = relationship("User", foreign_keys=[liked_id], backref="likes_received")
