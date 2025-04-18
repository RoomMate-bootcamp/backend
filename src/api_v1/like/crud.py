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
    query = select(Like).where(
        and_(
            Like.liker_id == liked_id,
            Like.liked_id == liker_id,
            Like.status != LikeStatus.DECLINED
        )
    )
    result = await session.execute(query)
    reverse_like = result.scalar_one_or_none()

    query = select(Like).where(
        and_(
            Like.liker_id == liker_id,
            Like.liked_id == liked_id
        )
    )
    result = await session.execute(query)
    existing_like = result.scalar_one_or_none()

    if existing_like:
        return existing_like, False, None

    new_like = Like(
        liker_id=liker_id,
        liked_id=liked_id,
        status=LikeStatus.PENDING,
        timestamp=datetime.utcnow()
    )
    session.add(new_like)
    await session.flush() 

    notification = None
    is_match = False

    if reverse_like and reverse_like.status == LikeStatus.PENDING:
        new_like.status = LikeStatus.ACCEPTED
        reverse_like.status = LikeStatus.ACCEPTED
        is_match = True

        liker = await session.get(User, liker_id)
        notification = Notification(
            user_id=liked_id,
            type=NotificationType.MATCH_CREATED,
            content=f"У вас с {liker.name} схожие интересы! Теперь вы можете общаться.",
            related_user_id=liker_id,
            related_entity_id=new_like.id,
            timestamp=datetime.utcnow()
        )
        session.add(notification)
    else:
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
    like = await session.get(Like, like_id)
    if not like or like.liked_id != user_id:
        return None, None, None

    if accept:
        like.status = LikeStatus.ACCEPTED

        query = select(Like).where(
            and_(
                Like.liker_id == user_id,
                Like.liked_id == like.liker_id
            )
        )
        result = await session.execute(query)
        reverse_like = result.scalar_one_or_none()

        if reverse_like:
            reverse_like.status = LikeStatus.ACCEPTED

            liker = await session.get(User, user_id)
            notification = Notification(
                user_id=like.liker_id,
                type=NotificationType.MATCH_CREATED,
                content=f"У вас с {liker.name} схожие интересы! Теперь вы можете общаться.",
                related_user_id=user_id,
                related_entity_id=like.id,
                timestamp=datetime.utcnow()
            )
            session.add(notification)
            await session.commit()
            return like, reverse_like, notification
        else:
            reverse_like = Like(
                liker_id=user_id,
                liked_id=like.liker_id,
                status=LikeStatus.ACCEPTED,
                timestamp=datetime.utcnow()
            )
            session.add(reverse_like)

            liker = await session.get(User, user_id)
            notification = Notification(
                user_id=like.liker_id,
                type=NotificationType.MATCH_CREATED,
                content=f"У вас с {liker.name} схожие интересы! Теперь вы можете общаться.",
                related_user_id=user_id,
                related_entity_id=like.id,
                timestamp=datetime.utcnow()
            )
            session.add(notification)
            await session.commit()
            return like, reverse_like, notification
    else:
        like.status = LikeStatus.DECLINED
        await session.commit()
        return like, None, None


async def get_received_likes(
        session: AsyncSession, user_id: int, status: Optional[LikeStatus] = None
) -> List[Like]:
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
    query = select(Like).where(
        and_(
            Like.liker_id == user_id,
            Like.status == LikeStatus.ACCEPTED
        )
    ).order_by(Like.timestamp.desc())

    result = await session.execute(query)
    return result.scalars().all()


async def get_notifications(session: AsyncSession, user_id: int) -> Tuple[List[Notification], int]:
    query = select(Notification).where(
        Notification.user_id == user_id
    ).order_by(Notification.timestamp.desc())

    result = await session.execute(query)
    notifications = result.scalars().all()

    unread_count = sum(1 for n in notifications if not n.is_read)

    return notifications, unread_count


async def mark_as_read(session: AsyncSession, notification_id: int, user_id: int) -> bool:
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != user_id:
        return False

    notification.is_read = True
    await session.commit()
    return True


async def mark_all_as_read(session: AsyncSession, user_id: int) -> int:
    query = update(Notification).where(
        and_(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    ).values(is_read=True)

    result = await session.execute(query)
    await session.commit()
    return result.rowcount
