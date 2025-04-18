from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from src.api_v1.user.schemas import RoommateResponse


class LikeStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class LikeCreate(BaseModel):
    liked_id: int


class LikeResponse(BaseModel):
    id: int
    liker_id: int
    liked_id: int
    status: LikeStatus
    timestamp: datetime
    liker: Optional[RoommateResponse] = None
    liked: Optional[RoommateResponse] = None

    class Config:
        from_attributes = True


class LikeAction(BaseModel):
    action: str = Field(..., pattern="^(accept|decline)$")


class NotificationType(str, Enum):
    NEW_LIKE = "new_like"
    MATCH_CREATED = "match_created"
    NEW_MESSAGE = "new_message"


class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    content: str
    related_user_id: Optional[int] = None
    related_entity_id: Optional[int] = None
    is_read: bool
    timestamp: datetime
    related_user: Optional[RoommateResponse] = None

    class Config:
        from_attributes = True


class NotificationsResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int