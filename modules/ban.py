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
    if not message.reply_to_message:
        await message.reply("⚠️ Вы должны ответить на сообщение пользователя, которого хотите забанить")
        return

    admins = await bot.get_chat_administrators(message.chat.id)
    admin_ids = [admin.user.id for admin in admins]

    target_user = message.reply_to_message.from_user
    if target_user and target_user.id in admin_ids:
        await message.reply("⚠️ Пользователь является админом в данной группе")
        return

    reason = message.text.split(' ', 1)[1] if ' ' in message.text else "Не указана"

    target_id = target_user.id if target_user else 0
    try:
        await bot.ban_chat_member(message.chat.id, target_id)
    except Exception:
        await message.reply("⚠️ Не удалось забанить пользователя. Возможно, у бота нет разрешения")
        return

    await message.reply(
        f"""
#BAN
Админ: {utils.wrap_actor_link(message)}
Пользователь: {utils.wrap_actor_link(message.reply_to_message)}
Причина: {reason}""",
        link_preview_options=types.LinkPreviewOptions(is_disabled=True),
    )


@router.message(Command('unban'))
@filters.only_groups
@auth.require_auth(level=200)
async def unban_user(message: types.Message, bot: Bot):
    try:
        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id if message.reply_to_message.from_user else 0
            await bot.unban_chat_member(message.chat.id, target_id)
            await message.reply(
                f"""
#UNBAN
Админ: {utils.wrap_actor_link(message)}
Пользователь: {utils.wrap_actor_link(message.reply_to_message)}""",
                link_preview_options=types.LinkPreviewOptions(is_disabled=True),
            )
        else:
            await message.reply("⚠️ Вы должны ответить на сообщение пользователя, которого хотите разбанить")
    except Exception:
        await d.send_view_traceback(message, traceback.format_exc(), bot)
