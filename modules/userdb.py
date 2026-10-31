"""Модуль для добавления пользователей в БД"""

from aiogram import Router, types, Bot, F

from modules import botdebug as d
from modules import mysql_adapter as sql
from modules import utils

router = Router()
QUERY_CACHE: list[tuple[int, int]] = []


async def add_user_cache(userid: int, chatid: int) -> None:
    """Кэширует пользователя и пачкой сохраняет в БД при достижении лимита"""
    QUERY_CACHE.append((userid, chatid))

    if len(QUERY_CACHE) >= 20:
        batch = list(set(QUERY_CACHE))
        QUERY_CACHE.clear()
        try:
            await sql.add_user_many(batch)
        except Exception:
            pass


@router.message(F.new_chat_members)
@d.bugreport
async def new_member_handler(message: types.Message, bot: Bot):
    """Добавляет нового пользователя в базу данных и приветствует его"""
    hellomsg = await sql.get_group_hello(message.chat.id)

    for new_member in message.new_chat_members:
        if new_member.id in (utils.BOT_ID, 777000):
            continue

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
    """Убирает пользователя из базы данных при выходе из чата."""
    if message.left_chat_member:
        await sql.remove_user(message.left_chat_member.id, message.chat.id)


@d.bugreport
async def message_handler(message: types.Message, bot: Bot):
    """Добавляет пользователей в базу данных при получении сообщения"""
    if message.chat.type != "private":
        if not message.from_user or message.from_user.id in (utils.BOT_ID, 777000):
            return
        await add_user_cache(message.from_user.id, message.chat.id)
