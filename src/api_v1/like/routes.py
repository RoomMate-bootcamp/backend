from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.crud import get_current_active_user
from src.api_v1.like.schemas import (
    LikeCreate,
    LikeResponse,
    LikeAction,
    LikeStatus,
    NotificationResponse,
    NotificationsResponse,
)
from src.api_v1.like import crud as like_crud
from src.core.database import User, postgres_helper, Notification

likes_router = APIRouter(prefix="/likes", tags=["Likes"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@likes_router.post("", response_model=LikeResponse, status_code=status.HTTP_201_CREATED)
async def create_like(
    like_data: LikeCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    liked_user = await session.get(User, like_data.liked_id)
    if not liked_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if current_user.id == like_data.liked_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot like yourself",
        )

    like, is_match, _ = await like_crud.create_like(
        session=session, liker_id=current_user.id, liked_id=like_data.liked_id
    )

    like.liker = current_user
    like.liked = liked_user

    return like


@likes_router.get("/received", response_model=List[LikeResponse])
async def get_received_likes(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
    status: LikeStatus = None,
):

    likes = await like_crud.get_received_likes(
        session=session, user_id=current_user.id, status=status
    )

    for like in likes:
        if not like.liker:
            like.liker = await session.get(User, like.liker_id)

    return likes


@likes_router.get("/sent", response_model=List[LikeResponse])
async def get_sent_likes(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
    status: LikeStatus = None,
):
    likes = await like_crud.get_sent_likes(
        session=session, user_id=current_user.id, status=status
    )

    for like in likes:
        if not like.liked:
            like.liked = await session.get(User, like.liked_id)

    return likes


@likes_router.get("/matches", response_model=List[LikeResponse])
async def get_matches(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    likes = await like_crud.get_matches(session=session, user_id=current_user.id)

    for like in likes:
        if not like.liked:
            like.liked = await session.get(User, like.liked_id)

    return likes


@likes_router.post("/{like_id}/respond", response_model=LikeResponse)
async def respond_to_like(
    like_id: int,
    action: LikeAction,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    accept = action.action == "accept"

    like, _, _ = await like_crud.respond_to_like(
        session=session, like_id=like_id, user_id=current_user.id, accept=accept
    )

    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found or you're not authorized to respond to it",
        )

    if not like.liker:
        like.liker = await session.get(User, like.liker_id)

    return like


@notifications_router.get("", response_model=NotificationsResponse)
async def get_notifications(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    notifications, unread_count = await like_crud.get_notifications(
        session=session, user_id=current_user.id
    )
    for notification in notifications:
        if notification.related_user_id and not notification.related_user:
            notification.related_user = await session.get(
                User, notification.related_user_id
            )

    return NotificationsResponse(notifications=notifications, unread_count=unread_count)


@notifications_router.post(
    "/{notification_id}/read", response_model=NotificationResponse
)
async def mark_notification_as_read(
    notification_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    """Mark a notification as read."""
    success = await like_crud.mark_as_read(
        session=session, notification_id=notification_id, user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or you're not authorized to mark it as read",
        )

    notification = await session.get(Notification, notification_id)

    if notification.related_user_id and not notification.related_user:
        notification.related_user = await session.get(
            User, notification.related_user_id
        )

    return notification


@notifications_router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    """Mark all notifications as read."""
    await like_crud.mark_all_as_read(session=session, user_id=current_user.id)
