"""Модуль для мута и размута пользователей"""

import time
import traceback
from datetime import timedelta

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import auth
from modules import botdebug as d
from modules import filters
from modules import utils

router = Router()

@router.message(Command("mute"))
@d.bugreport
@filters.only_groups
@filters.no_groups
@auth.require_auth(level=100)
async def mute_command(message: types.Message, bot: Bot):
    """
    [command]
    display = "/mute"
    description = \"\"\"Замутить пользователя. Нужно ответить на сообщение пользователя, \
    которого надо замутить и прописать команду в таком формате "/mute *число**единица времени* причина". \
    Если время больше чем год, то пользователь мутится навсегда. \
    Пример: "/mute 1d спам" - замутить на один день по причине спам.
    Доступные единицы времени:
    m - минуты
    h - часы
    d - дни
    w - недели\"\"\"
    """

    args = message.text.split()[1:]
    if len(args) < 1:
        await message.reply("⚠️ Использование: /mute время причина")
        return

    if message.reply_to_message:
        admins = await bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in admins]

        if utils.BOT_ID not in admin_ids:
            await message.reply("⚠️ Недостаточно прав для изменения разрешений пользователя")
            return

        if message.reply_to_message.from_user.id in admin_ids:
            await message.reply("⚠️ Пользователь является админом в данной супергруппе")
            return

        if message.reply_to_message.sender_chat:
            await bot.ban_chat_sender_chat(message.chat.id, message.reply_to_message.sender_chat.id)
            await message.reply(
                "🔇 Пользователь теперь больше не может писать от имени своих каналов. \
Чтобы замутить его, пропишите /mute на пользователя, а не на канал"
            )
            return

        time_arg = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else "Не указана"

        try:
            time_value = int(time_arg[:-1])
        except ValueError:
            await message.reply("⚠️ Время должно быть числом")
            return

        time_unit = time_arg[-1]

        # Да тут сплошная отсылка на дельтарун
        if time_unit == "s":
            mute_time = time_value
            time_unit = "секунд"
        elif time_unit == 'm':
            mute_time = timedelta(minutes=time_value).total_seconds()
            time_unit = "минут"
        elif time_unit == 'h':
            mute_time = timedelta(hours=time_value).total_seconds()
            time_unit = "часов"
        elif time_unit == 'd':
            mute_time = timedelta(days=time_value).total_seconds()
            time_unit = "дней"
        elif time_unit == 'w':
            mute_time = timedelta(weeks=time_value).total_seconds()
            time_unit = "недель"
        else:
            await message.reply(
                "⚠️ Некорректный формат времени. \
Пример: 10m - 10 минут, 2h - 2 часа, 5d - дней, 9w - 9 недель"
            )
            return

        unmute_time = time.time() + mute_time

        await bot.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            types.ChatPermissions(can_send_messages=False),
            until_date=unmute_time
        )

        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Отмена",
                        callback_data=f"unmute:{message.reply_to_message.from_user.id}",
                        style="danger"
                    )
                ]
            ]
        )

        if unmute_time >= time.time() + 31_536_000:
            unmute_time_str = "Замучен навсегда (время больше чем год)"
        else:
            unmute_time_str = f"Размут <tg-time unix=\"{unmute_time}\" format=\"r\">обновите тг</tg-time>"

        await message.reply(
                f"""
#MUTE
Админ: {utils.wrap_actor_link(message)}
Пользователь: {utils.wrap_actor_link(message.reply_to_message)}
{unmute_time_str}
Причина: {reason}""",
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=markup
            )
    else:
        await message.reply(
            "⚠️ Вы должны ответить на сообщение пользователя, \
которого хотите замутить"
        )

@router.message(Command('unmute'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=100)
async def unmute_command(message: types.Message, bot: Bot):
    """Команда /unmute для размута пользователей"""
    if message.reply_to_message:
        admins = await bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in admins]

        if utils.BOT_ID not in admin_ids:
            await message.reply("⚠️ Недостаточно прав для изменения разрешений пользователя")
            return

        if message.reply_to_message.from_user.id in admin_ids:
            await message.reply("⚠️ Пользователь является админом")
            return

        if message.reply_to_message.sender_chat:
            await bot.unban_chat_sender_chat(
                message.chat.id,
                message.reply_to_message.sender_chat.id
            )
            await message.reply("🔊 Пользователь теперь может писать от имени своих каналов. \
Чтобы размутить его, пропишите /unmute на пользователя, а не на канал")
            return

        try:
            await bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                types.ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_edit_tag=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_topics=True
                )
            )
        except:
            await message.reply(
                "⚠️ Не удалось изменить права пользователя. \
Убедитесь, что у бота есть разрешение на это"
            )
            return

        await message.reply(
            f"""
#UNMUTE
Админ: {utils.wrap_actor_link(message)}
Пользователь: {utils.wrap_actor_link(message.reply_to_message)}""",
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Вы должны ответить на сообщение пользователя, \
которого хотите размутить.")

async def callback_query(call: types.CallbackQuery, bot: Bot):
    try:
        if call.data.startswith("unmute"):
            command, userid = call.data.split(":")

            result = await auth.authorize_callback_query(call, bot, level=100)

            if result != 1:
                await call.answer(auth.randomise_errors(), show_alert=True)
                return

            await bot.restrict_chat_member(
                call.message.chat.id,
                userid,
                types.ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_edit_tag=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_topics=True
                )
            )

            await call.answer("Готово!")
            await call.message.edit_text(f"{call.message.html_text}\n⚠️ Действие отменено")
    except:
        await d.send_view_traceback(
            call.message,
            traceback.format_exc(),
            bot,
            func="callback_query"
        )
