"""Модуль тем оформления сообщений бота"""

import re

from aiogram import Router, types, Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.filters import Command
from aiogram.methods import SendMessage, EditMessageText
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

from modules import auth
from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql

router = Router()


async def wrap_emoji(chatid, text: str, force_theme=None) -> str:
    """Заменяет стандартные эмодзи на тему чата или принудительно указанную тему"""
    if isinstance(force_theme, dict):
        theme = force_theme
    elif force_theme is not None:
        theme = await sql.get_theme(force_theme)
    elif chatid and str(chatid)[0] != "-":
        theme = await sql.get_theme(0)
    else:
        theme = await sql.get_group_theme(chatid)

    if not theme:
        theme = await sql.get_theme(0)
        if not theme:
            return text

    if theme.get("is_premium"):
        emoji_replacement = {
            "<icon_preview>": f'<tg-emoji emoji-id="{theme["icon"]}">⚠️</tg-emoji>',
            "⚠️": f'<tg-emoji emoji-id="{theme["error"]}">⚠️</tg-emoji>',
            "🔇": f'<tg-emoji emoji-id="{theme["muted"]}">🔇</tg-emoji>',
            "🔊": f'<tg-emoji emoji-id="{theme["unmuted"]}">🔊</tg-emoji>',
            "📢": f'<tg-emoji emoji-id="{theme["report"]}">📢</tg-emoji>',
            "🚫": f'<tg-emoji emoji-id="{theme["banned"]}">🚫</tg-emoji>',
            "✅": f'<tg-emoji emoji-id="{theme["unbanned"]}">✅</tg-emoji>',
            "🍺": f'<tg-emoji emoji-id="{theme["beer"]}">🍺</tg-emoji>',
            "⏳": f'<tg-emoji emoji-id="{theme["wait"]}">⏳</tg-emoji>',
        }
    else:
        emoji_replacement = {
            "<icon_preview>": theme.get("icon", "⚠️"),
            "⚠️": theme.get("error", "⚠️"),
            "🔇": theme.get("muted", "🔇"),
            "🔊": theme.get("unmuted", "🔊"),
            "📢": theme.get("report", "📢"),
            "🚫": theme.get("banned", "🚫"),
            "✅": theme.get("unbanned", "✅"),
            "🍺": theme.get("beer", "🍺"),
            "⏳": theme.get("wait", "⏳"),
        }

    keys = sorted(emoji_replacement.keys(), key=len, reverse=True)
    pattern = re.compile(r'(<tg-emoji[^>]*>.*?</tg-emoji>)|(' + '|'.join(map(re.escape, keys)) + ')')

    def _replace(m: re.Match) -> str:
        if m.group(1):
            return m.group(1)
        return emoji_replacement.get(m.group(2), m.group(2))

    return pattern.sub(_replace, text)


@router.message(Command("set_theme"))
@d.bugreport
@filters.cooldown
@auth.require_auth(level=100)
@filters.only_groups
async def set_theme_command(message: types.Message, bot: Bot):
    args = message.text.split() if message.text else []

    if len(args) < 2:
        await message.reply(await wrap_emoji(message.chat.id, "⚠️ Укажите номер темы"), parse_mode="HTML")
        return

    try:
        await sql.set_group_theme(message.chat.id, args[1])
    except ValueError:
        await message.reply(await wrap_emoji(message.chat.id, "⚠️ Темы с данным номером не существует"), parse_mode="HTML")
        return

    sql.THEME_CACHE.pop(message.chat.id, None)
    sql.THEME_CACHE.pop((message.chat.id,), None)

    await message.react([types.ReactionTypeEmoji(emoji="👍")])


@router.message(Command("view_themes", "themes"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def view_themes_command(message: types.Message, bot: Bot):
    themes = await sql.get_themes()

    strings = ["Доступные темы: ", ""]

    for theme in themes:
        strings.append(f"Номер: {theme['id']}")
        strings.append(f"   Название: {theme['name']}")
        strings.append(f"   Описание: {theme['description']}")
        strings.append(await wrap_emoji(message.chat.id, "   Предпросмотр: <icon_preview>", force_theme=theme))
        strings.append("")

    await message.reply("\n".join(strings), parse_mode="HTML")


class ThemeMiddleware(BaseRequestMiddleware):
    async def __call__(
        self,
        make_request,
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ):
        if isinstance(method, (SendMessage, EditMessageText)):
            text = getattr(method, "text", None)
            if text and "Доступные темы:" not in text:
                chat_id = getattr(method, "chat_id", None)
                if chat_id and str(chat_id)[0] == "-":
                    method.text = await wrap_emoji(chat_id, text)
                else:
                    method.text = await wrap_emoji(chat_id, text, force_theme=0)

        return await make_request(bot, method)
