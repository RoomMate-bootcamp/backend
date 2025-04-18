from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.crud import get_current_active_user
from src.api_v1.match.schemas import MatchResponse, MatchWithUserResponse, MatchesResponse
from src.core.database import User, postgres_helper
from src.core.database.alchemy_models.match import Match

matches_router = APIRouter(prefix="/matches", tags=["Matches"])


@matches_router.post("/{roommate_id}", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
        roommate_id: int,
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    query = select(User).where(User.id == roommate_id)
    result = await session.execute(query)
    roommate = result.scalar_one_or_none()

    if not roommate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roommate not found",
        )

    query = select(Match).where(
        (
                (Match.user1_id == current_user.id) & (Match.user2_id == roommate_id) |
                (Match.user1_id == roommate_id) & (Match.user2_id == current_user.id)
        )
    )
    result = await session.execute(query)
    existing_match = result.scalar_one_or_none()

    if existing_match:
        return existing_match

    new_match = Match(
        user1_id=current_user.id,
        user2_id=roommate_id,
        timestamp=datetime.utcnow(),
    )

    session.add(new_match)
    await session.commit()
    await session.refresh(new_match)

    return new_match


@matches_router.get("/", response_model=List[MatchWithUserResponse])
async def get_matches(
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    query = select(Match).where(
        (Match.user1_id == current_user.id) | (Match.user2_id == current_user.id)
    )
    result = await session.execute(query)
    matches = result.scalars().all()

    match_responses = []
    for match in matches:
        roommate_id = match.user2_id if match.user1_id == current_user.id else match.user1_id

        query = select(User).where(User.id == roommate_id)
        result = await session.execute(query)
        roommate = result.scalar_one_or_none()

        if roommate:
            match_response = MatchWithUserResponse(
                id=match.id,
                timestamp=match.timestamp,
                roommate=roommate
            )
            match_responses.append(match_response)

    return match_responses


@matches_router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(
        match_id: int,
        current_user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    query = select(Match).where(
        (Match.id == match_id) &
        ((Match.user1_id == current_user.id) | (Match.user2_id == current_user.id))
    )
    result = await session.execute(query)
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    await session.delete(match)
    await session.commit()
