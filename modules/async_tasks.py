import asyncio

from aiogram import Bot
from aiogram import types
from cachetools import TTLCache

from modules import utils

groups_cache = TTLCache(maxsize=500, ttl=300)

async def can_delete_messages(chatid: int, bot: Bot):
    if chatid in groups_cache:
        return groups_cache[chatid]

    bot_perms = await bot.get_chat_member(chatid, utils.BOT_ID)

    if bot_perms.status == "administrator":
        result = bot_perms.can_delete_messages
    else:
        result = False

    groups_cache[chatid] = result

    return result

async def delete_msg(message: types.Message, bot: Bot, delay=5):
    if await can_delete_messages(message.chat.id, bot):
        await asyncio.sleep(delay)
        await message.delete()
