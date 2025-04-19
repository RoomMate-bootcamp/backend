from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.ai_matching.schemas import (
    AIMatchesResponse,
    AIMatchResponse,
    CompatibilityScore,
)
from src.api_v1.auth.crud import get_current_active_user
from src.core.database import User, postgres_helper
from src.core.database.alchemy_models.match import Match
from src.core.utils.AIMatchingService import ai_matching_service

ai_matching_router = APIRouter(prefix="/ai-matching", tags=["AI Matching"])


@ai_matching_router.get("/smart-matches", response_model=AIMatchesResponse)
async def get_ai_matches(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
    limit: int = Query(10, ge=1, le=50),
):

    if not current_user.name or not current_user.bio or not current_user.interests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your profile to get AI matches",
        )

    query = select(Match).where(
        ((Match.user1_id == current_user.id) | (Match.user2_id == current_user.id))
    )
    result = await session.execute(query)
    matches = result.scalars().all()

    matched_user_ids = []
    for match in matches:
        if match.user1_id == current_user.id:
            matched_user_ids.append(match.user2_id)
        else:
            matched_user_ids.append(match.user1_id)

    query = select(User).where(
        (User.id != current_user.id) & (~User.id.in_(matched_user_ids))
    )
    result = await session.execute(query)
    potential_matches = result.scalars().all()

    ai_matches = ai_matching_service.get_top_matches(
        current_user=current_user, potential_matches=potential_matches, limit=limit
    )

    matches_response = AIMatchesResponse(
        matches=[
            AIMatchResponse(
                user=match["user"],
                compatibility_score=match["compatibility_score"],
                compatibility_explanation=match["compatibility_explanation"],
            )
            for match in ai_matches
        ]
    )

    return matches_response


@ai_matching_router.get("/{user_id}/compatibility", response_model=CompatibilityScore)
async def get_compatibility_score(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    other_user = result.scalar_one_or_none()

    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    score, explanation = ai_matching_service.calculate_compatibility_score(
        current_user, other_user
    )

    return CompatibilityScore(score=score, explanation=explanation)
