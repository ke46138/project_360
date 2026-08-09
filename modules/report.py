"""Модуль с системой репортов"""

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import utils

router = Router()

@router.message(Command('report'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def report(message: types.Message, bot: Bot):
    """Отправляет жалобы администраторам"""
    if message.reply_to_message:
        if message.sender_chat:
            user_id = message.sender_chat.id
        elif message.from_user:
            user_id = message.from_user.id
        else:
            await message.reply("⚠️ Ошибка: не удалось определить отправителя")
            return

        if user_id == message.reply_to_message.from_user.id:
            await message.reply("⚠️ Саморепорт запрещён")
            return

        bot_admins = await sql.get_group_admins(message.chat.id, bot)

        if message.reply_to_message.from_user.id == utils.BOT_ID:
            await message.reply("⚠️ Репорт бота запрещён")
            return

        for i in bot_admins:
            if i[0] == user_id and i[1] >= 100:
                await message.reply("⚠️ Репорт админов запрещён")
                return

        report_text = message.text.split(" ", 1)[1] if " " in message.text else "Не указано"
        fullname_from = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        fullname_to = f"{message.reply_to_message.from_user.first_name} \
{message.reply_to_message.from_user.last_name or ''}".strip()

        for i in bot_admins:
            if i[1] >= 100:
                try:
                    await bot.send_message(
                        i[0],
                        f"""
📢 <b>Новая жалоба</b>

От: <a href=\"tg://user?id={message.from_user.id}\">{fullname_from}</a>
На: <a href=\"tg://user?id={message.reply_to_message.from_user.id}\">{fullname_to}</a>
Текст сообщения: "{message.reply_to_message.text}"
Ссылка на сообщение: <a href="https://telegram.me/c/{str(message.chat.id)[4:]}/{message.reply_to_message.message_id}">Тыкъ</a>
Причина: {report_text}
""",
                        parse_mode='HTML'
                    )
                except:
                    continue

        await message.reply(
            f"📢 На пользователя \
<a href=\"tg://user?id={message.reply_to_message.from_user.id}\">{fullname_to}</a> \
была отправлена жалоба",
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Вы должны ответить на сообщение пользователя, \
на которого хотите отправить жалобу")
