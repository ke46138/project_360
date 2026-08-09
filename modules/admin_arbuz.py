from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import auth
from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql

FORCE_RANDOM_VALUE = False

router = Router()

@router.message(Command('force_random'))
@d.bugreport
@filters.cooldown
@auth.require_auth
async def force_random_command(message: types.Message, bot: Bot):
    global FORCE_RANDOM_VALUE

    args = message.text.split()

    if len(args) < 2:
        await message.reply("⚠️ Введите число, которое хотите принудительно установить в качестве рандома")
        return

    try:
        value = int(args[1])
    except:
        await message.reply("⚠️ Введите число, которое хотите принудительно установить в качестве рандома")
        return

    FORCE_RANDOM_VALUE = value

    await message.react([types.ReactionTypeEmoji(emoji='👍')])

@router.message(Command('force_marriage'))
@d.bugreport
@filters.cooldown
@auth.require_auth
async def force_marriage_command(message: types.Message, bot: Bot):
    args = message.text.split()

    if len(args) < 3:
        await message.reply("⚠️ Введите два id пользователей, которых хотите принудительно поженить")
        return

    try:
        first = int(args[1])
        second = int(args[2])
    except:
        await message.reply("⚠️ Введите два id пользователей, которых хотите принудительно поженить")
        return

    await sql.add_marriage(message.chat.id, first, second)

    await message.react([types.ReactionTypeEmoji(emoji='👍')])
