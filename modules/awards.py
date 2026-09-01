from aiogram import Router, types, Bot
from aiogram.filters import Command

from petrovich.enums import Case

from modules import auth
from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import utils

router: Router = Router()

@router.message(Command("award"))
@d.bugreport
@filters.cooldown
@filters.only_groups
@auth.require_auth(level=100)
async def award_command(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply(
            "⚠️ Вы должны ответить на сообщение пользователя, которому хотите выдать награду"
        )
        return

    args = message.text.split() # /award level text

    if len(args) < 3:
        await message.reply("⚠️ Неверные аргументы. Использование: /award уровень_награды текст награды")
        return

    level, text = args[2], " ".join(args[3:])

    try:
        level = int(level)
    except ValueError:
        await message.reply("⚠️ Уровень должен быть числом")
        return

    if level > 100:
        await message.reply("⚠️ Слишком большой уровень награды")
        return

    if level < 1:
        await message.reply("⚠️ Слишком низкий уровень награды")
        return

    if len(text) > 500:
        await message.reply("⚠️ Слишком большой текст награды")
        return

    await sql.add_group_user_award(message.chat.id, message.from_user.id, message.reply_to_message.from_user.id, level, text)

    await message.reply(f"🏅{level} Награда вручена {utils.wrap_actor_link(message.reply_to_message, True, Case.DATIVE)}")

@router.message(Command("awards"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def awards_command(message: types.Message, bot: Bot):
    if message.reply_to_message and message.reply_to_message.from_user.id != 777000: # type: ignore
        target = message.reply_to_message.from_user.id # type: ignore
        string = [f"🏆 Награды {utils.wrap_actor_link(message, incline=True, case=Case.ACCUSATIVE)}:", ""]
    else:
        target = message.from_user.id # type: ignore
        string = ["🏆 Ваши награды:", ""]

    awards = await sql.get_group_user_awards(message.chat.id, target)

    i = 1
    for award in awards:
        string.append(f"{i}. 🏅{award['level']} {award['text']} | <tg-time unix=\"{award['issued_at']}\" format=\"dT\">обновите тг</tg-time>")
        i += 1

    if len(string) == 2:
        await message.reply("⚠️ Наград нет")
    else:
        await message.reply("\n".join(string))
