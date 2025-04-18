from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey, String, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.alchemy_models.base import Base


class NotificationType(str, PyEnum):
    NEW_LIKE = "new_like"
    MATCH_CREATED = "match_created"
    NEW_MESSAGE = "new_message"


class Notification(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    content: Mapped[str] = mapped_column(String)
    related_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    related_entity_id: Mapped[int] = mapped_column(nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], backref="notifications")
    related_user = relationship("User", foreign_keys=[related_user_id])
