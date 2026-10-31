"""Фильтр ссылок"""

import asyncio
import re
from urllib.parse import urlparse

from aiogram import Router
from cachetools import TTLCache

from modules import async_tasks
from modules import auth
from modules import mysql_adapter as sql

router = Router()
cache = TTLCache(maxsize=512, ttl=900)
domains_cache = TTLCache(maxsize=512, ttl=300)
URL_PATTERN = re.compile(r'https?://[\w./?-]+')


def set_cached_status(chatid: int, enabled: bool) -> None:
    """Записывает в кэш состояние фильтра ссылок"""
    cache[chatid] = 1 if enabled else 0


def normalize_domain(raw: str) -> str:
    """Извлекает и нормализует имя домена из текста или ссылки"""
    raw = raw.strip().lower()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    domain = parsed.netloc or parsed.path
    domain = domain.split("/")[0].split(":")[0].strip().strip(".")
    return domain


def invalidate_domains_cache(chatid: int) -> None:
    """Сбрасывает кэш разрешённых доменов для указанного чата"""
    domains_cache.pop(chatid, None)


async def get_allowed_domains(chatid: int) -> set[str]:
    """Возвращает объединённый набор глобальных и локальных доменов чата"""
    if chatid in domains_cache:
        return domains_cache[chatid]

    domains = {d.lower() for d in await sql.get_group_allowed_urls(chatid)}
    domains_cache[chatid] = domains
    return domains


def is_domain_allowed(domain: str, allowed_domains: set[str]) -> bool:
    """Проверяет принадлежность домена к списку разрешённых"""
    domain = domain.lower()
    if domain in allowed_domains:
        return True
    return any(domain.endswith("." + allowed) for allowed in allowed_domains)


def check_links_allowed(text: str, allowed_domains: set[str]) -> bool:
    """Проверяет, все ли ссылки в тексте принадлежат разрешённым доменам"""
    for match in URL_PATTERN.findall(text):
        parsed_url = urlparse(match)
        domain = parsed_url.netloc.lower()

        if not is_domain_allowed(domain, allowed_domains):
            return False

    return True


async def is_enabled(chatid: int) -> int:
    """Проверяет, включён ли фильтр ссылок в указанном чате"""
    if chatid in cache:
        return cache[chatid]

    result = await sql.get_urlfilter_enabled(chatid)
    cache[chatid] = result
    return result


async def filter_msg(message, bot):
    """Фильтрует ссылки от пользователей в группах"""
    if message.chat.type == "private" or not message.text:
        return

    if await is_enabled(message.chat.id) == 1:
        allowed_domains = await get_allowed_domains(message.chat.id)
        if not check_links_allowed(message.text, allowed_domains):
            result = await auth.authorize(message, bot, level=100)
            if result == 1:
                return

            warn_message = await message.reply("⚠️ [[ГИПЕРССЫЛКА ЗАБЛОКИРОВАНА]]")
            asyncio.create_task(async_tasks.delete_msg(message, bot, delay=1))
            asyncio.create_task(async_tasks.delete_msg(warn_message, bot))
