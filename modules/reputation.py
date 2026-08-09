import time

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import utils

router = Router()

@router.message(Command("add_rep"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def add_rep_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == message.from_user.id:
            await message.reply("⚠️ Самому себе репутации добавить нельзя")
            return

        user = await sql.get_reputation_user(message.chat.id, message.from_user.id)

        if user["last_add_time"] + 3600 > time.time():
            await message.reply(f"⏳ Подождите ещё {utils.format_remaining_time(user['last_add_time'] + 3600 - time.time())}")
            return

        await sql.increment_reputation_user(message.chat.id, message.reply_to_message.from_user.id, message.from_user.id)
        await message.react([types.ReactionTypeEmoji(emoji="👍")])
    else:
        await message.reply("⚠️ Вы должны ответить на сообщение пользователя, которому хотите оказать уважение")

@router.message(Command("dec_rep"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def dec_rep_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == message.from_user.id:
            await message.reply("⚠️ Самому себе репутации убавить нельзя")
            return

        user = await sql.get_reputation_user(message.chat.id, message.from_user.id)

        if user["last_add_time"] + 3600 > time.time():
            await message.reply(
                f"<tg-emoji emoji-id=\"5240106125436683458\">⏳</tg-emoji> Подождите ещё {utils.format_remaining_time(user['last_add_time'] + 3600 - time.time())}",
                parse_mode="HTML"
            )
            return

        await sql.decrement_reputation_user(message.chat.id, message.reply_to_message.from_user.id, message.from_user.id)
        await message.react([types.ReactionTypeEmoji(emoji="👍")])
    else:
        await message.reply("⚠️ Вы должны ответить на сообщение пользователя, которому хотите убавить репутации")

@router.message(Command("my_rep"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def my_rep_command(message: types.Message, bot: Bot):
    user = await sql.get_reputation_user(message.chat.id, message.from_user.id)

    await message.reply(f"Ваша репутация: {user['reputation']}")
