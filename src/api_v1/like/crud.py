from datetime import datetime
from typing import List, Tuple, Optional

from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.alchemy_models.like import Like, LikeStatus
from src.core.database.alchemy_models.notification import Notification, NotificationType
from src.core.database.alchemy_models.user import User


async def create_like(
        session: AsyncSession, liker_id: int, liked_id: int
) -> Tuple[Like, bool, Optional[Notification]]:
    """
    Create a like from one user to another.
    Returns the like, whether it created a match, and any notification created.
    """
    # Check if the reverse like already exists (other user already liked this user)
    query = select(Like).where(
        and_(
            Like.liker_id == liked_id,
            Like.liked_id == liker_id,
            Like.status != LikeStatus.DECLINED
        )
    )
    result = await session.execute(query)
    reverse_like = result.scalar_one_or_none()

    # Check if this like already exists
    query = select(Like).where(
        and_(
            Like.liker_id == liker_id,
            Like.liked_id == liked_id
        )
    )
    result = await session.execute(query)
    existing_like = result.scalar_one_or_none()

    if existing_like:
        # Already liked, just return it
        return existing_like, False, None

    # Create the new like
    new_like = Like(
        liker_id=liker_id,
        liked_id=liked_id,
        status=LikeStatus.PENDING,
        timestamp=datetime.utcnow()
    )
    session.add(new_like)
    await session.flush()  # Flush to get the ID

    notification = None
    is_match = False

    if reverse_like and reverse_like.status == LikeStatus.PENDING:
        # It's a match! Update both likes to ACCEPTED
        new_like.status = LikeStatus.ACCEPTED
        reverse_like.status = LikeStatus.ACCEPTED
        is_match = True

        # Create match notification for the other user
        liker = await session.get(User, liker_id)
        notification = Notification(
            user_id=liked_id,
            type=NotificationType.MATCH_CREATED,
            content=f"Вы и {liker.name} совпали! Теперь вы можете общаться.",
            related_user_id=liker_id,
            related_entity_id=new_like.id,
            timestamp=datetime.utcnow()
        )
        session.add(notification)
    else:
        # Create like notification for the liked user
        liker = await session.get(User, liker_id)
        notification = Notification(
            user_id=liked_id,
            type=NotificationType.NEW_LIKE,
            content=f"{liker.name} проявил(а) интерес к вам!",
            related_user_id=liker_id,
            related_entity_id=new_like.id,
            timestamp=datetime.utcnow()
        )
        session.add(notification)

    await session.commit()
    return new_like, is_match, notification


async def respond_to_like(
        session: AsyncSession, like_id: int, user_id: int, accept: bool
) -> Tuple[Like, Optional[Like], Optional[Notification]]:
    """
    Respond to a like. If accepted and it creates a match, also returns the other like and a notification.
    """
    # Get the like
    like = await session.get(Like, like_id)
    if not like or like.liked_id != user_id:
        return None, None, None

    if accept:
        like.status = LikeStatus.ACCEPTED

        # Check if the user has already liked the other user
        query = select(Like).where(
            and_(
                Like.liker_id == user_id,
                Like.liked_id == like.liker_id
            )
        )
        result = await session.execute(query)
        reverse_like = result.scalar_one_or_none()

        if reverse_like:
            # It's a match! Update the reverse like too
            reverse_like.status = LikeStatus.ACCEPTED

            # Create match notification
            liker = await session.get(User, user_id)
            notification = Notification(
                user_id=like.liker_id,
                type=NotificationType.MATCH_CREATED,
                content=f"Вы и {liker.name} совпали! Теперь вы можете общаться.",
                related_user_id=user_id,
                related_entity_id=like.id,
                timestamp=datetime.utcnow()
            )
            session.add(notification)
            await session.commit()
            return like, reverse_like, notification
        else:
            # Create a new like in the reverse direction
            reverse_like = Like(
                liker_id=user_id,
                liked_id=like.liker_id,
                status=LikeStatus.ACCEPTED,
                timestamp=datetime.utcnow()
            )
            session.add(reverse_like)

            # Create match notification
            liker = await session.get(User, user_id)
            notification = Notification(
                user_id=like.liker_id,
                type=NotificationType.MATCH_CREATED,
                content=f"Вы и {liker.name} совпали! Теперь вы можете общаться.",
                related_user_id=user_id,
                related_entity_id=like.id,
                timestamp=datetime.utcnow()
            )
            session.add(notification)
            await session.commit()
            return like, reverse_like, notification
    else:
        # Decline the like
        like.status = LikeStatus.DECLINED
        await session.commit()
        return like, None, None


async def get_received_likes(
        session: AsyncSession, user_id: int, status: Optional[LikeStatus] = None
) -> List[Like]:
    """Get likes received by a user, optionally filtered by status."""
    if status:
        query = select(Like).where(
            and_(
                Like.liked_id == user_id,
                Like.status == status
            )
        ).order_by(Like.timestamp.desc())
    else:
        query = select(Like).where(
            Like.liked_id == user_id
        ).order_by(Like.timestamp.desc())

    result = await session.execute(query)
    return result.scalars().all()


async def get_sent_likes(
        session: AsyncSession, user_id: int, status: Optional[LikeStatus] = None
) -> List[Like]:
    """Get likes sent by a user, optionally filtered by status."""
    if status:
        query = select(Like).where(
            and_(
                Like.liker_id == user_id,
                Like.status == status
            )
        ).order_by(Like.timestamp.desc())
    else:
        query = select(Like).where(
            Like.liker_id == user_id
        ).order_by(Like.timestamp.desc())

    result = await session.execute(query)
    return result.scalars().all()


async def get_matches(session: AsyncSession, user_id: int) -> List[Like]:
    """Get all successful matches for a user."""
    query = select(Like).where(
        and_(
            Like.liker_id == user_id,
            Like.status == LikeStatus.ACCEPTED
        )
    ).order_by(Like.timestamp.desc())

    result = await session.execute(query)
    return result.scalars().all()


async def get_notifications(session: AsyncSession, user_id: int) -> Tuple[List[Notification], int]:
    """Get all notifications for a user and count of unread ones."""
    query = select(Notification).where(
        Notification.user_id == user_id
    ).order_by(Notification.timestamp.desc())

    result = await session.execute(query)
    notifications = result.scalars().all()

    # Count unread
    unread_count = sum(1 for n in notifications if not n.is_read)

    return notifications, unread_count


async def mark_as_read(session: AsyncSession, notification_id: int, user_id: int) -> bool:
    """Mark a notification as read."""
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != user_id:
        return False

    notification.is_read = True
    await session.commit()
    return True


async def mark_all_as_read(session: AsyncSession, user_id: int) -> int:
    """Mark all notifications for a user as read. Returns number of updated notifications."""
    query = update(Notification).where(
        and_(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    ).values(is_read=True)

    result = await session.execute(query)
    await session.commit()
    return result.rowcount
