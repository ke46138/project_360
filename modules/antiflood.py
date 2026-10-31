"""Модуль защиты от флуда в группах"""

from datetime import timedelta
import time

from aiogram import types, Bot

from modules import botdebug as d
from modules import filters
from modules import redis
from modules import mysql_adapter as sql
from modules import utils


@d.bugreport
@filters.only_groups
async def message_handler(message: types.Message, bot: Bot):
    if not message.from_user:
        return

    if not await sql.get_antiflood_enabled(message.chat.id):
        return

    key = f"flood:{message.chat.id}:{message.from_user.id}"
    result = await redis.incr_key(key, ttl=timedelta(seconds=10))

    if result >= 10:
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if user.status == "administrator":
            return

        unmute_time = int(time.time() + 60)
        try:
            await bot.restrict_chat_member(
                message.chat.id,
                message.from_user.id,
                types.ChatPermissions(can_send_messages=False),
                until_date=unmute_time
            )
        except Exception:
            await message.reply("⚠️ Сработал антифлуд, но не удалось замутить пользователя")
            return

        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Отмена",
                        callback_data=f"unmute:{message.from_user.id}",
                        style="danger"
                    )
                ]
            ]
        )

        await message.reply(
            f"🔇 Пользователь {utils.wrap_user_link(message.from_user.full_name, message.from_user.id)} "
            f"замучен автоматически за спам. Размут "
            f'<tg-time unix="{unmute_time}" format="r">обновите тг</tg-time>',
            reply_markup=markup,
            parse_mode="HTML"
        )
