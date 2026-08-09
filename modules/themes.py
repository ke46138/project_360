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

async def wrap_emoji(chatid, text, force_theme=None):
    if force_theme:
        theme = await sql.get_theme(force_theme)
    elif str(chatid)[0] != "-":
        theme = await sql.get_theme(0)
    else:
        theme = await sql.get_group_theme(chatid)

    if theme["is_premium"]:
        emoji_replacement = {
            "<icon_preview>": f"<tg-emoji emoji-id=\"{theme['icon']}\">⚠️</tg-emoji>",
            "⚠️": f"<tg-emoji emoji-id=\"{theme['error']}\">⚠️</tg-emoji>",
            "🔇": f"<tg-emoji emoji-id=\"{theme['muted']}\">🔇</tg-emoji>",
            "🔊": f"<tg-emoji emoji-id=\"{theme['unmuted']}\">🔊</tg-emoji>",
            "📢": f"<tg-emoji emoji-id=\"{theme['report']}\">📢</tg-emoji>",
            "🚫": f"<tg-emoji emoji-id=\"{theme['banned']}\">🚫</tg-emoji>",
            "✅": f"<tg-emoji emoji-id=\"{theme['unbanned']}\">✅</tg-emoji>",
            "🍺": f"<tg-emoji emoji-id=\"{theme['beer']}\">🍺</tg-emoji>",
            "⏳": f"<tg-emoji emoji-id=\"{theme['wait']}\">⏳</tg-emoji>",
        }
    else:
        emoji_replacement = {
            "<icon_preview>": theme["icon"],
            "⚠️": theme["error"],
            "🔇": theme["muted"],
            "🔊": theme["unmuted"],
            "📢": theme["report"],
            "🚫": theme["banned"],
            "✅": theme["unbanned"],
            "🍺": theme["beer"],
            "⏳": theme["wait"]
        }

    pattern = re.compile("|".join(map(re.escape, emoji_replacement.keys())))

    return pattern.sub(lambda m: emoji_replacement[m.group(0)], text)

@router.message(Command("set_theme"))
@d.bugreport
@filters.cooldown
@auth.require_auth(level=100)
@filters.only_groups
async def set_theme_command(message: types.Message, bot: Bot):
    args = message.text.split()

    if len(args) < 2:
        await message.reply(await wrap_emoji(message.chat.id, "⚠️ Укажите номер темы"), parse_mode="HTML")
        return

    try:
        await sql.set_group_theme(message.chat.id, args[1])
    except ValueError:
        await message.reply(await wrap_emoji(message.chat.id, "⚠️ Темы с данным номером не существует"), parse_mode="HTML")
        return
    sql.THEME_CACHE.pop(args[1], None)

    await message.react([types.ReactionTypeEmoji(emoji="👍")])

@router.message(Command("view_themes"))
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
        strings.append(await wrap_emoji(message.chat.id, f"   Предпросмотр: <icon_preview>", force_theme=theme["id"]))

    await message.reply("\n".join(strings), parse_mode="HTML")

class ThemeMiddleware(BaseRequestMiddleware):
    async def __call__(
        self,
        make_request,
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ):
        if isinstance(method, SendMessage) or isinstance(method, EditMessageText):
            if str(method.chat_id)[0] == "-":
                method.text = await wrap_emoji(method.chat_id, method.text)
            else:
                method.text = await wrap_emoji(method.chat_id, method.text, force_theme=0)

        return await make_request(bot, method)
