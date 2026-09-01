import random
import time

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import utils

router = Router()

BEER_STRINGS = [
    "Пейте пиво «Милкивэй» — будет детям веселей!",
    "Если пьёте водку «Марс» — зашибенно всё у вас!",
    "Пейте вино «Баунти» — вражины будут в ауте!",
    "Глотни разок ликёр «Пикник» — здоровьем зарядишься вмиг!",
    "Наливайте ром «Кит-Кат» — каждый станет вам как брат!",
    "Одна бутылка виски «Твикс» — и в голове безумный микс!",
    "Плесни в себя текилу «Натс» — АРЕЩЬКИ станешь сей же час!",
    "Пролей на мир бурбон «Лион» — и всё погрузит в хаос он!"
]

@router.message(Command("beer"))
@d.bugreport # Аахахаххахахахаха буковки
@filters.cooldown # Ахахаха я сюда два кулдауна навесил
@filters.only_groups
@filters.only_sentry_instance
async def beer_command(message: types.Message, bot: Bot):
    values = await sql.get_user_beer(message.chat.id, message.from_user.id)

    if values["last_drink"] + 3600 > time.time():
        await message.reply(
            f"⏳ Подождите ещё {utils.format_remaining_time(values['last_drink'] + 3600 - time.time())}"
        )
        return

    drinked = round(random.randint(500, 50000) / 1000, 2)

    await sql.add_drinked_beer_user(message.chat.id, message.from_user.id, drinked)

    await message.reply(
        f"""
🍺 Вы выпили {drinked} литров пива

Следующая попытка через час.
{random.choice(BEER_STRINGS)}
""",
    parse_mode="HTML"
    )

@router.message(Command("beer_top"))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.only_sentry_instance
async def beer_top_command(message: types.Message, bot: Bot):
    top_users = await sql.get_top_beer_users(message.chat.id)

    msg = "📊 Топ 10 пивозавров чата:\n\n"
    i = 1

    for user in top_users:
        try:
            user_info = await bot.get_chat_member(message.chat.id, user["userid"])
        except:
            await sql.delete_from_beer(user["userid"], message.chat.id)
            continue

        msg += f"{i}. \
{utils.wrap_user_link(user_info.user.full_name, user_info.user.id)}, \
выпито {user['drinkedtotal']} литров пива\n"
        i += 1

    if msg != "📊 Топ 10 пивозавров чата:\n\n":
        await message.reply(msg, parse_mode="HTML", disable_notification=True)
    else:
        await message.reply(
            "⚠️ Никто пока не пил пиво (вот и хорошо). Таблица лидеров пуста"
        )
