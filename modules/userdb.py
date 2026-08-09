"""Модуль для добавления пользователей в бд"""

from aiogram import Router, types, Bot, F

from modules import botdebug as d
from modules import mysql_adapter as sql
from modules import utils

router = Router()
QUERY_CACHE = []

async def add_user_cache(userid, chatid):
    QUERY_CACHE.append(
        (userid, chatid,)
    )

    if len(QUERY_CACHE) > 20:
        await sql.add_user_many(QUERY_CACHE)

@router.message(F.new_chat_members)
@d.bugreport
async def new_member_handler(message: types.Message, bot: Bot):
    """Добавляет пользователя в базу данных"""
    hellomsg = await sql.get_group_hello(message.chat.id)

    for new_member in message.new_chat_members:
        if new_member.id in (utils.BOT_ID, 777000):
            return

        await sql.add_user(new_member.id, message.chat.id)

        if hellomsg:
            await message.reply(
                hellomsg.replace(
                    "{name}",
                    utils.wrap_user_link(new_member.full_name, new_member.id)
                ),
                parse_mode="HTML"
            )

@router.message(F.left_chat_member)
@d.bugreport
async def member_left(message: types.Message, bot: Bot):
    """Убирает пользователя из базы данных"""
    await sql.remove_user(message.left_chat_member.id, message.chat.id)

@d.bugreport
async def message_handler(message: types.Message, bot: Bot):
    """Добаляет пользователей в базу данных при получении сообщения"""
    global QUERY_CACHE

    if message.chat.type != "private":
        if message.from_user.id in (utils.BOT_ID, 777000):
            return
        await add_user_cache(message.from_user.id, message.chat.id)
