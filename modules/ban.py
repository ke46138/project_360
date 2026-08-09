import traceback
from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import auth
from modules import filters
from modules import botdebug as d
from modules import utils

router = Router()

@router.message(Command('ban'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def ban_user(message: types.Message, bot: Bot):
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == 6562915401 and message.chat.id == -1002298339941:
            await message.reply("⚠️ Абрикос, ТЫ ЗАЕБАЛ БАНИТЬ ЙЕЛОУКИТТЕН ПРОСТО ТАК")
            return

        if message.reply_to_message.from_user.id == 1312172800 and message.chat.id == -1002298339941:
            await message.reply("⚠️ Нет :)")
            return

        admins = await bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in admins]

        if message.reply_to_message.from_user.id in admin_ids:
            await message.reply("⚠️ Пользователь является админом в данной группе")
            return

        reason = message.text.split(' ', 1)[1] if ' ' in message.text else "Не указана"

        try:
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        except:
            await message.reply("⚠️ Не удалось забанить пользователя. Возможно, у бота нет разрешения")
            return

        await message.reply(
            f"""
#BAN
Админ: {utils.wrap_actor_link(message)}
Пользователь: {utils.wrap_actor_link(message.reply_to_message)}
Причина: {reason}""",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Вы должны ответить на сообщение пользователя, \
которого хотите забанить.")

@router.message(Command('unban'))
@filters.only_groups
@auth.require_auth(level=200)
async def unban_user(message: types.Message, bot: Bot):
    try:
        if message.reply_to_message:
            await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            await message.reply(
                f"""
#UNBAN
Админ: {utils.wrap_actor_link(message)}
Пользователь: {utils.wrap_actor_link(message.reply_to_message)}""",
                disable_web_page_preview=True
            )
        else:
            await message.reply("⚠️ Вы должны ответить на сообщение пользователя, \
которого хотите разбанить.")
    except:
        await d.send_view_traceback(message, traceback.format_exc(), bot)
