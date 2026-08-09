"""Модуль предложки функций"""

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import auth
from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql

router: Router = Router()

@router.message(Command('suggest'))
@d.bugreport
@filters.cooldown
async def suggest_command(message: types.Message, bot: Bot):
    if not message.text or len(message.text.split(maxsplit=1)) < 2:
        await message.reply("⚠️ Использование: /suggest <описание функции>")
        return

    suggestion_text = message.text.split(maxsplit=1)[1].strip()
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    if len(suggestion_text) >= 1000:
        await message.reply("⚠️ Предложение не должно быть длинее 1000 символов")
        return

    await sql.add_suggestion(user_id, username, suggestion_text)

    await message.react([types.ReactionTypeEmoji(emoji='👍')])

@router.message(Command('suggestions'))
@d.bugreport
@filters.cooldown
@auth.require_auth
async def suggestions_command(message: types.Message, bot: Bot):
    results = await sql.get_all_suggestions()

    if not results:
        await message.reply("⚠️ Пока никто ничего не предложил")
        return

    formatted = "\n\n".join(
        [f"🆔 {row['id']} — от @{row['username']}\n💡 {row['text']}" for row in results]
    )

    if len(formatted) > 3500:
        formatted = formatted[:3500] + "\n\n... (дальше обрезано)"

    await message.reply(f"📋 Список предложений:\n\n{formatted}")
