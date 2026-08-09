"""Фильтр ссылок"""

import asyncio
import re
from urllib.parse import urlparse

from aiogram import Router
from cachetools import TTLCache

import config
from modules import async_tasks
from modules import auth
from modules import mysql_adapter as sql

router = Router()
cache = TTLCache(maxsize=512, ttl=900)

def check_links_allowed(text: str) -> bool:
    """
    Проверяет, все ли ссылки в тексте принадлежат разрешённым доменам.

    :param text: Строка с текстом, содержащим ссылки.
    :return: True, если все ссылки разрешены, иначе False.
    """
    url_pattern = re.compile(r'https?://[\w./?-]+')

    for match in url_pattern.findall(text):
        parsed_url = urlparse(match)
        domain = parsed_url.netloc

        if domain not in config.URL_ALLOWLIST:
            return False

    return True

async def is_enabled(chatid):
    if chatid in cache:
        return cache[chatid]

    result = await sql.get_urlfilter_enabled(chatid)

    cache[sql] = result
    return result

async def filter_msg(message, bot):
    """Фильтрует ссылки от пользователей"""
    if message.chat.type != "private":
        if message.text:
            if await is_enabled(message.chat.id) == 1:
                allowed_links = check_links_allowed(message.text)
                if not allowed_links:
                    result = await auth.authorize(message, bot, level=100)

                    if result == 1:
                        return

                    warn_message = await message.reply("⚠️ [[Ссылка заблокирована]]")
                    await asyncio.create_task(async_tasks.delete_msg(message, bot, delay=1))
                    await asyncio.create_task(async_tasks.delete_msg(warn_message, bot))
