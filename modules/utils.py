from dateutil.relativedelta import relativedelta
from datetime import datetime
from html import escape
from urllib.parse import quote_plus

from aiogram import Bot, types
from petrovich.main import Petrovich
from petrovich.enums import Case

BOT_ID = 0
BOT_USERNAME = ""

petrovich = Petrovich()

def wrap_user_link(fullname: str, userid: int | str):
    return f"<a href=\"tg://user?id={userid}\">{escape(fullname)}</a>"

def wrap_actor_link(message: types.Message, incline=False, case=Case.GENITIVE):
    if incline:
        fullname = escape(incline_name(message, case))
    else:
        fullname = escape(message.sender_chat.title if message.sender_chat else message.from_user.full_name) # type: ignore
    if message.sender_chat and message.from_user.id != 777000:
        return f"<a href=\"https://telegram.me/{message.sender_chat.username}\">{fullname}</a>"
    return f"<a href=\"tg://user?id={message.from_user.id}\">{fullname}</a>"

def wrap_actor_link_user(user: types.ResultChatMemberUnion, incline=False, case=Case.GENITIVE):
    if incline:
        fullname = escape(incline_name_user(user, case))
    else:
        fullname = escape(user.user.full_name)

    return f"<a href=\"tg://user?id={user.user.id}\">{fullname}</a>"

def incline_name(message: types.Message, case):
    if message.sender_chat:
        return petrovich.firstname(message.sender_chat.title, case)
    return f"{petrovich.firstname(message.from_user.first_name, case)} \
{petrovich.lastname(message.from_user.last_name, case) \
if message.from_user.last_name else ""}".strip()

def incline_name_user(user: types.ResultChatMemberUnion, case):
    return f"{petrovich.firstname(user.user.first_name, case)} \
{petrovich.lastname(user.user.last_name, case) \
if user.user.last_name else ""}".strip()

async def set_bot_id(bot: Bot):
    global BOT_ID, BOT_USERNAME

    profile = await bot.get_me()
    BOT_ID = profile.id
    BOT_USERNAME = profile.username

def build_redis_url(host, port, password, db, username=None):
    encoded_password = quote_plus(password)

    if username:
        auth = f"{quote_plus(username)}:{encoded_password}"
    else:
        auth = f":{encoded_password}"

    return f"redis://{auth}@{host}:{port}/{db}"

def plural_ru(value: int, forms: tuple[str, str, str]) -> str:
    if value % 10 == 1 and value % 100 != 11:
        form = forms[0]
    elif 2 <= value % 10 <= 4 and not (12 <= value % 100 <= 14):
        form = forms[1]
    else:
        form = forms[2]
    return f"{value} {form}"

def humanize_timestamp(ts: int, now_override=None) -> str:
    """
    Принимает таймстамп и возвращает строку вида:
    "1 год 5 месяцев 2 недели 2 дня 23 часа 53 минуты 12 секунд"
    """
    now = now_override or datetime.now()
    past = datetime.fromtimestamp(ts)
    delta = relativedelta(now, past) # Дельтарун отсылко

    weeks, days = divmod(delta.days, 7)

    parts = []
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

def format_remaining_time(total_seconds: int) -> str:
    """
    Преобразует секунды в человекочитаемую строку
    с корректными склонениями.
    """
    if total_seconds < 0:
        total_seconds = 0

    hours = round(total_seconds // 3600)
    minutes = round((total_seconds % 3600) // 60)
    seconds = round(total_seconds % 60, 2)

    if hours > 0:
        return (
            f"{plural_ru(hours, ('час', 'часа', 'часов'))}, "
            f"{plural_ru(minutes, ('минута', 'минуты', 'минут'))} и "
            f"{plural_ru(seconds, ('секунда', 'секунды', 'секунд'))}"
        )
    if minutes > 0 >= hours:
        return (
            f"{plural_ru(minutes, ('минута', 'минуты', 'минут'))} и "
            f"{plural_ru(seconds, ('секунда', 'секунды', 'секунд'))}"
        )
    else:
        return (
            f"{plural_ru(seconds, ('секунда', 'секунды', 'секунд'))}"
        )
