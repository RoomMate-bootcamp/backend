from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.crud import get_current_active_user
from src.api_v1.user.schemas import ProfileResponse, ProfileUpdate, RoommateResponse
from src.core.database import User, postgres_helper, Like
from src.core.database.alchemy_models.match import Match

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@users_router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    for key, value in profile.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)

    await session.commit()
    await session.refresh(current_user)

    return current_user


@users_router.get("/roommates", response_model=List[RoommateResponse])
async def get_potential_roommates(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
    # Add optional filter parameters
    min_budget: Optional[int] = Query(None, description="Minimum rent budget"),
    max_budget: Optional[int] = Query(None, description="Maximum rent budget"),
    location: Optional[str] = Query(None, description="Preferred location filter"),
    min_cleanliness: Optional[int] = Query(
        None, ge=1, le=5, description="Minimum cleanliness level"
    ),
    gender: Optional[str] = Query(None, description="Filter by gender"),
):
    """Get potential roommates with parameter-based filtering"""

    # Get users that are already matched
    query = select(Match).where(
        or_(Match.user1_id == current_user.id, Match.user2_id == current_user.id)
    )
    result = await session.execute(query)
    matches = result.scalars().all()

    matched_user_ids = []
    for match in matches:
        if match.user1_id == current_user.id:
            matched_user_ids.append(match.user2_id)
        else:
            matched_user_ids.append(match.user1_id)

    # Get users that you have already liked
    query = select(Like).where(Like.liker_id == current_user.id)
    result = await session.execute(query)
    likes = result.scalars().all()

    liked_user_ids = [like.liked_id for like in likes]

    # Combine all user IDs to exclude
    exclude_ids = matched_user_ids + liked_user_ids + [current_user.id]

    # Start building filter criteria
    filter_criteria = [(User.id.not_in(exclude_ids)), User.is_active == True]

    # Add optional filters if specified
    if min_budget is not None:
        filter_criteria.append(User.rent_budget >= min_budget)

    if max_budget is not None:
        filter_criteria.append(User.rent_budget <= max_budget)

    if location is not None:
        filter_criteria.append(User.location.ilike(f"%{location}%"))

    if min_cleanliness is not None:
        filter_criteria.append(User.cleanliness_level >= min_cleanliness)

    if gender is not None:
        filter_criteria.append(User.gender == gender)

    # Build and execute query with all filters
    query = select(User).where(and_(*filter_criteria))
    result = await session.execute(query)
    potential_roommates = result.scalars().all()

    return potential_roommates
