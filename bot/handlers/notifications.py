import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update, text

from src.core.database import User, postgres_helper, Notification
from src.core.database.alchemy_models.notification import NotificationType
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.keyboards.matches_kb import get_match_actions_keyboard

router = Router()
logger = logging.getLogger(__name__)


async def check_notifications(user_id: int, bot):
    """Check and send pending notifications for a user"""
    try:
        async with postgres_helper.session_factory() as session:
            query = (
                select(Notification)
                .where(
                    (Notification.user_id == user_id) & (Notification.is_read == False)
                )
                .order_by(Notification.timestamp.desc())
            )

            result = await session.execute(query)
            notifications = result.scalars().all()

            if not notifications:
                return

            query = text(
                "SELECT user_metadata->>'telegram_id' AS telegram_id FROM users WHERE id = :user_id"
            )
            result = await session.execute(query, {"user_id": user_id})
            row = result.fetchone()

            if not row or not row[0]:
                logger.warning(
                    f"Cannot send notification: User {user_id} has no Telegram ID"
                )
                return

            telegram_id = row[0]

            for notification in notifications:
                if notification.type == NotificationType.NEW_LIKE:
                    if notification.related_user_id:
                        liker = await session.get(User, notification.related_user_id)
                        if liker:
                            liker_name = liker.name or "Пользователь"
                            liker_age = f", {liker.age}" if liker.age else ""
                            liker_gender = f", {liker.gender}" if liker.gender else ""
                            liker_info = f"{liker_name}{liker_age}{liker_gender}"
                        else:
                            liker_info = "Кто-то"
                    else:
                        liker_info = "Кто-то"

                    message = (
                        f"❤️ *У вас новый лайк!*\n\n"
                        f"{liker_info} проявил(а) интерес к вам!\n\n"
                        f'Посмотрите вкладку "Мои совпадения", чтобы узнать больше.'
                    )

                    keyboard = types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(
                                    text="👀 Посмотреть совпадения",
                                    callback_data="show_matches",
                                )
                            ]
                        ]
                    )

                elif notification.type == NotificationType.MATCH_CREATED:
                    if notification.related_user_id:
                        partner = await session.get(User, notification.related_user_id)
                        if partner:
                            partner_name = partner.name or "Пользователь"
                            partner_age = f", {partner.age}" if partner.age else ""
                            partner_gender = (
                                f", {partner.gender}" if partner.gender else ""
                            )
                            partner_info = (
                                f"{partner_name}{partner_age}{partner_gender}"
                            )
                        else:
                            partner_info = "Кто-то"
                    else:
                        partner_info = "Кто-то"

                    message = (
                        f"✨ *У вас новое совпадение!*\n\n"
                        f"Вы и {partner_info} проявили взаимный интерес друг к другу!\n"
                        f"Теперь вы можете начать общение и обсудить возможность совместной аренды жилья."
                    )

                    keyboard = types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(
                                    text="💬 Посмотреть совпадения",
                                    callback_data="show_matches",
                                )
                            ]
                        ]
                    )

                else:
                    message = notification.content
                    keyboard = get_main_menu_keyboard()

                try:
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )

                    notification.is_read = True
                except Exception as e:
                    logger.error(f"Failed to send notification to {telegram_id}: {e}")

            if notifications:
                await session.commit()
                logger.info(
                    f"Sent {len(notifications)} notifications to user {user_id}"
                )

    except Exception as e:
        logger.error(f"Error in check_notifications: {e}")


async def show_notification_list(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await message.answer(
            "Пожалуйста, используйте /start для начала работы с ботом."
        )
        return

    async with postgres_helper.session_factory() as session:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.timestamp.desc())
            .limit(10)
        )

        result = await session.execute(query)
        notifications = result.scalars().all()

        if not notifications:
            await message.answer(
                "У вас нет уведомлений.", reply_markup=get_main_menu_keyboard()
            )
            return

        notification_text = "📬 *Ваши последние уведомления:*\n\n"

        for i, notification in enumerate(notifications, 1):
            if notification.type == NotificationType.NEW_LIKE:
                type_text = "❤️ Новый лайк"
            elif notification.type == NotificationType.MATCH_CREATED:
                type_text = "✨ Новое совпадение"
            else:
                type_text = "📝 Уведомление"

            timestamp = notification.timestamp.strftime("%d.%m.%Y %H:%M")

            status = "👁️ Просмотрено" if notification.is_read else "🆕 Новое"

            notification_text += (
                f"{i}. {type_text} - {timestamp} ({status})\n{notification.content}\n\n"
            )

        await message.answer(
            notification_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )


def register_notifications_handlers(dp):
    dp.include_router(router)

    router.message.register(show_notification_list, Command("notifications"))
