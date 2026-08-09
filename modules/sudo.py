"""Модуль для выполнения действий от имени бота"""

import traceback

from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.types import ReactionTypeEmoji

from modules import auth
from modules import botdebug as d

router = Router()

@router.message(Command('sudo'))
@auth.require_auth
async def sudo(message: types.Message, bot: Bot):
    """Команда /sudo, позволяет писать от имени бота"""
    try:
        args = message.text.split()

        if len(args) <= 3:
            await message.reply("""⚠️ Недостаточно аргументов.
Использование: /sudo bot действие аргументы действия""")
            return

        full_message = ""
        index = 0

        if args[1] == "bot":
            if args[2] == "sendMessage":
                if len(args) <= 4:
                    await message.reply("""⚠️ Недостаточно аргументов.
Использование: /sudo bot sendMessage chatid сообщение""")
                    return

                full_message = " ".join(args[4:])

                await bot.send_message(
                    args[3],
                    full_message,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            elif args[2] == "replyToMessage":
                if len(args) <= 5:
                    await message.reply("""⚠️ Недостаточно аргументов.
Использование: /sudo bot replyToMessage messageId chatid сообщение""")
                    return

                full_message = " ".join(args[5:])

                await bot.send_message(
                    args[4],
                    full_message,
                    reply_to_message_id=int(args[3]),
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            elif args[2] == "deleteMsg":
                if len(args) <= 4:
                    await message.reply("""⚠️ Недостаточно аргументов.
Использование: /sudo bot deleteMsg messageId chatid""")
                    return

                await bot.delete_message(args[4], args[3])
            else:
                await message.reply("⚠️ Неверный аргумент действие.")
                return
        else:
            await message.reply("⚠️ Неверный аргумент от кого.")
            return

        await message.react([ReactionTypeEmoji(emoji='👍')])
    except:
        await d.send_view_traceback(message, traceback.format_exc(), bot)
