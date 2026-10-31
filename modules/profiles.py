"""Модуль профилей пользователей"""

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
    if message.sender_chat and getattr(message.from_user, "id", None) != 777000:
        await message.reply("⚠️ Недоступно от имени группы")
        return

    description = " ".join(message.text.split()[1:]) if message.text else ""

    user_id = message.from_user.id if message.from_user else 0
    await sql.set_group_user_description(message.chat.id, user_id, description)

    await message.react([types.ReactionTypeEmoji(emoji="👍")])


@router.message(Command("profile"))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def profile_command(message: types.Message, bot: Bot):
    target_message = message.reply_to_message if message.reply_to_message else message

    if target_message.sender_chat:
        chat_type = target_message.sender_chat.type
        type_names = {
            "group": "группы",
            "supergroup": "супергруппы",
            "channel": "канала",
        }
        user_type = type_names.get(chat_type, "неизвестно")

        await message.reply(f"""
👤 Ник: {utils.wrap_actor_link(target_message)}
Является телеграм админом этого чата с включённой анонимностью, от имени {user_type}
Имеет фиксированный уровень доступа 200

Остальная статистика недоступна
""")
    else:
        target_user_id = target_message.from_user.id if target_message.from_user else 0
        user = await bot.get_chat_member(message.chat.id, target_user_id)

        status_map = {
            "creator": "Создатель чата",
            "administrator": "Телеграм админ чата",
            "left": "Вышел из чата/никогда не был в чате",
            "kicked": "Забанен",
        }
        tg_admin_text = status_map.get(user.status, "Обычный пользователь")

        admins = await sql.get_group_admins(message.chat.id, bot)
        admin_entry = next((item for item in admins if item[0] == target_user_id), None)

        if admin_entry:
            admin_text = f"Имеет уровень доступа {admin_entry[1]}"
        else:
            admin_text = "Не имеет прав администратора"

        marriage_raw = await sql.get_marriages_user(message.chat.id, target_user_id)

        if marriage_raw:
            partner_id = (
                marriage_raw['second_id']
                if marriage_raw['first_id'] == target_user_id
                else marriage_raw['first_id']
            )
            partner = await bot.get_chat_member(message.chat.id, partner_id)
            marriage = f"Брак с {utils.wrap_user_link(partner.user.full_name, partner_id)}"
        else:
            marriage = "Не состоит в браке"

        rep_data = await sql.get_reputation_user(message.chat.id, target_user_id)
        reputation = rep_data.get("reputation", 0) if isinstance(rep_data, dict) else 0

        credits_data = await sql.get_user_social_credits(target_user_id, message.chat.id)
        money = credits_data.get("credits", 0) if isinstance(credits_data, dict) else 0

        beer_data = await sql.get_user_beer(message.chat.id, target_user_id)
        beer_drinked = beer_data.get("drinkedtotal", 0) if isinstance(beer_data, dict) else 0

        desc_text = await sql.get_group_user_description(message.chat.id, target_user_id)

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
            link_preview_options=types.LinkPreviewOptions(is_disabled=True),
        )
