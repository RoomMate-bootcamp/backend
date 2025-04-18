from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from src.api_v1.user.schemas import RoommateResponse


class MatchBase(BaseModel):
    user1_id: int
    user2_id: int
    timestamp: datetime


class MatchCreate(BaseModel):
    user_id: int


class MatchResponse(MatchBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MatchWithUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    roommate: RoommateResponse


class MatchesResponse(BaseModel):
    matches: list[MatchWithUserResponse]
