from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import utils

router = Router()

@router.message(Command("set_my_desc"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def set_my_desc_command(message: types.Message, bot: Bot):
    if message.sender_chat and message.sender_chat != 777000:
        await message.reply("⚠️ Недоступно от имени группы")
        return

    description = " ".join(message.text.split()[1:])

    await sql.set_group_user_description(message.chat.id, message.from_user.id, description)

    await message.react([types.ReactionTypeEmoji(emoji="👍")])

@router.message(Command("profile"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def profile_command(message: types.Message, bot: Bot):
    if message.reply_to_message and message.reply_to_message != 777000:
        target_message = message.reply_to_message
    else:
        target_message = message

    if target_message.sender_chat:
        if target_message.sender_chat.type == "group":
            user_type = "группы"
        elif target_message.sender_chat.type == "supergroup":
            user_type = "супергруппы"
        elif target_message.sender_chat.type == "channel":
            user_type = "канала"
        else:
            user_type = "неизвестно"

        await message.reply(f"""
👤 Ник: {utils.wrap_actor_link(target_message)}
Является телеграм админом этого чата с включённой анонимностью, от имени {user_type}
Имеет фиксированный уровень доступа 200

Остальная статистика недоступна
""")
    else:
        user = await bot.get_chat_member(message.chat.id, target_message.from_user.id)

        if user.status == "creator":
            tg_admin_text = "Создатель чата"
        elif user.status == "administrator":
            tg_admin_text = "Телеграм админ чата"
        elif user.status == "left":
            tg_admin_text = "Вышел из чата/никогда не был в чате"
        elif user.status == "kicked":
            tg_admin_text = "Забанен"
        else:
            tg_admin_text = "Обычный пользователь"

        admins = await sql.get_group_admins(message.chat.id, bot)

        pattern = [target_message.from_user.id]
        result = next(
            (item for item in admins if item[:len(pattern)] == pattern),
            None
        )

        if result:
            admin_text = f"Имеет уровень доступа {result[1]}"
        else:
            admin_text = "Не имеет прав администратора"

        marriage_raw = await sql.get_marriages_user(message.chat.id, target_message.from_user.id)

        if marriage_raw:
            if marriage_raw["first_id"] == target_message.from_user.id:
                marriage_user = await bot.get_chat_member(message.chat.id, marriage_raw["second_id"])
                marriage = f"Брак с {utils.wrap_user_link(marriage_user.user.full_name, marriage_raw["second_id"])}"
            else:
                marriage_user = await bot.get_chat_member(message.chat.id, marriage_raw["first_id"])
                marriage = f"Брак с {utils.wrap_user_link(marriage_user.user.full_name, marriage_raw["first_id"])}"
        else:
            marriage = "Не состоит в браке"

        reputation = (await sql.get_reputation_user(message.chat.id, target_message.from_user.id))["reputation"]
        money = (await sql.get_user_social_credits(target_message.from_user.id, message.chat.id))["credits"]
        beer_drinked = (await sql.get_user_beer(message.chat.id, target_message.from_user.id))["drinkedtotal"]
        desc_text = await sql.get_group_user_description(message.chat.id, target_message.from_user.id)

        await message.reply(
            f"""
👤 Ник: {utils.wrap_actor_link(target_message)}
{tg_admin_text}
{admin_text}
{desc_text}

{marriage}
Репутация: {reputation}
Денег в кошельке: {money} Т₽
Выпито пива: {beer_drinked} литров
""",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
