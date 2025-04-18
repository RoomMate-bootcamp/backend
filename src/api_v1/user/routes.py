from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.crud import get_current_active_user
from src.api_v1.user.schemas import ProfileResponse, ProfileUpdate, RoommateResponse
from src.core.database import User, postgres_helper

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
        current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@users_router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
        profile: ProfileUpdate,
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    # Update user profile
    for key, value in profile.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)

    await session.commit()
    await session.refresh(current_user)

    return current_user


@users_router.get("/roommates", response_model=List[RoommateResponse])
async def get_potential_roommates(
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    # Get users who could be potential roommates
    # Excluding the current user and users that have already been matched

    # First, get all matches for the current user
    from src.core.database.alchemy_models.match import Match

    # Get IDs of users who are already matched with the current user
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

    # Get potential roommates (excluding current user and matched users)
    query = select(User).where(
        (User.id != current_user.id) &
        (~User.id.in_(matched_user_ids))
    )
    result = await session.execute(query)
    potential_roommates = result.scalars().all()

    return potential_roommates
