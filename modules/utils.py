"""Вспомогательные утилиты для бота"""

from __future__ import annotations

from datetime import datetime
from html import escape
from urllib.parse import quote_plus

from aiogram import Bot, types
from dateutil.relativedelta import relativedelta
from petrovich.enums import Case
from petrovich.main import Petrovich

BOT_ID: int = 0
BOT_USERNAME: str = ""

petrovich = Petrovich()


def wrap_user_link(fullname: str, userid: int | str) -> str:
    """Формирует HTML ссылку на пользователя по его ID"""
    return f'<a href="tg://user?id={userid}">{escape(fullname)}</a>'


def wrap_actor_link(message: types.Message, incline: bool = False, case: Case = Case.GENITIVE) -> str:
    """Формирует HTML ссылку на автора сообщения (пользователя или чат)"""
    if incline:
        fullname = escape(incline_name(message, case))
    else:
        if message.sender_chat and message.sender_chat.title:
            fullname = escape(message.sender_chat.title)
        elif message.from_user:
            fullname = escape(message.from_user.full_name)
        else:
            fullname = "Пользователь"

    if message.sender_chat and (not message.from_user or message.from_user.id != 777000):
        if message.sender_chat.username:
            return f'<a href="https://telegram.me/{message.sender_chat.username}">{fullname}</a>'
        return fullname

    user_id = message.from_user.id if message.from_user else 0
    return f'<a href="tg://user?id={user_id}">{fullname}</a>'


def wrap_actor_link_user(user: types.ResultChatMemberUnion, incline: bool = False, case: Case = Case.GENITIVE) -> str:
    """Формирует HTML ссылку на объект ChatMember"""
    if incline:
        fullname = escape(incline_name_user(user, case))
    else:
        fullname = escape(user.user.full_name)

    return f'<a href="tg://user?id={user.user.id}">{fullname}</a>'


def incline_name(message: types.Message, case: Case) -> str:
    """Склоняет имя автора сообщения по падежам"""
    if message.sender_chat and message.sender_chat.title:
        return petrovich.firstname(message.sender_chat.title, case)

    if not message.from_user:
        return "Пользователь"

    first = petrovich.firstname(message.from_user.first_name, case) if message.from_user.first_name else ""
    last = petrovich.lastname(message.from_user.last_name, case) if message.from_user.last_name else ""
    return f"{first} {last}".strip() or "Пользователь"


def incline_name_user(user: types.ResultChatMemberUnion, case: Case) -> str:
    """Склоняет имя ChatMember по падежам"""
    first = petrovich.firstname(user.user.first_name, case) if user.user.first_name else ""
    last = petrovich.lastname(user.user.last_name, case) if user.user.last_name else ""
    return f"{first} {last}".strip() or "Пользователь"


async def set_bot_id(bot: Bot) -> None:
    """Сохраняет ID и username бота в глобальные переменные"""
    global BOT_ID, BOT_USERNAME
    profile = await bot.get_me()
    BOT_ID = profile.id
    BOT_USERNAME = profile.username or ""


def build_redis_url(host: str, port: int, password: str = "", db: int = 0, username: str = "") -> str:
    """Собирает URL для подключения к Redis."""
    encoded_password = quote_plus(password) if password else ""

    if username and encoded_password:
        auth = f"{quote_plus(username)}:{encoded_password}"
    elif encoded_password:
        auth = f":{encoded_password}"
    else:
        auth = ""

    auth_part = f"{auth}@" if auth else ""
    return f"redis://{auth_part}{host}:{port}/{db}"


def plural_ru(value: int, forms: tuple[str, str, str]) -> str:
    """Возвращает число и существительное в правильной русской форме"""
    abs_val = abs(value)
    if abs_val % 10 == 1 and abs_val % 100 != 11:
        form = forms[0]
    elif 2 <= abs_val % 10 <= 4 and not (12 <= abs_val % 100 <= 14):
        form = forms[1]
    else:
        form = forms[2]
    return f"{value} {form}"


def humanize_timestamp(ts: int | float, now_override: datetime | None = None) -> str:
    """Преобразует прошедший таймстамп в строку вида:
    '1 год 5 месяцев 2 недели 2 дня 23 часа 53 минуты 12 секунд'.
    """
    now = now_override or datetime.now()
    try:
        past = datetime.fromtimestamp(ts)
    except (ValueError, OSError, OverflowError):
        return f"{ts} секунд"

    delta = relativedelta(now, past)
    weeks, days = divmod(delta.days, 7)

    parts: list[str] = []
    if delta.years:
        parts.append(plural_ru(delta.years, ("год", "года", "лет")))
    if delta.months:
        parts.append(plural_ru(delta.months, ("месяц", "месяца", "месяцев")))
    if weeks:
        parts.append(plural_ru(weeks, ("неделя", "недели", "недель")))
    if days:
        parts.append(plural_ru(days, ("день", "дня", "дней")))
    if delta.hours:
        parts.append(plural_ru(delta.hours, ("час", "часа", "часов")))
    if delta.minutes:
        parts.append(plural_ru(delta.minutes, ("минута", "минуты", "минут")))
    if delta.seconds:
        parts.append(plural_ru(delta.seconds, ("секунда", "секунды", "секунд")))

    if len(parts) > 1:
        parts[-1] = f"и {parts[-1]}"

    return " ".join(parts) if parts else "0 секунд"


def format_remaining_time(total_seconds: int | float) -> str:
    """Преобразует секунды в человекочитаемую строку с корректными склонениями"""
    if total_seconds < 0:
        total_seconds = 0

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = round(total_seconds % 60, 2)

    if hours > 0:
        return (
            f"{plural_ru(hours, ('час', 'часа', 'часов'))}, "
            f"{plural_ru(minutes, ('минута', 'минуты', 'минут'))} и "
            f"{plural_ru(int(seconds), ('секунда', 'секунды', 'секунд'))}"
        )
    if minutes > 0:
        return (
            f"{plural_ru(minutes, ('минута', 'минуты', 'минут'))} и "
            f"{plural_ru(int(seconds), ('секунда', 'секунды', 'секунд'))}"
        )
    return plural_ru(int(seconds), ('секунда', 'секунды', 'секунд'))
