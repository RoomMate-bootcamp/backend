from typing import List, Optional
from pydantic import BaseModel, Field

from src.api_v1.user.schemas import RoommateResponse


class CompatibilityScore(BaseModel):
    score: float = Field(
        ..., ge=0, le=100, description="Compatibility score from 0-100"
    )
    explanation: str = Field(..., description="Explanation of compatibility factors")


class AIMatchResponse(BaseModel):
    user: RoommateResponse
    compatibility_score: float = Field(..., ge=0, le=100)
    compatibility_explanation: str

    class Config:
        from_attributes = True


class AIMatchesRequest(BaseModel):
    limit: Optional[int] = Field(
        10, ge=1, le=50, description="Maximum number of matches to return"
    )


class AIMatchesResponse(BaseModel):
    matches: List[AIMatchResponse]

    class Config:
        from_attributes = True
