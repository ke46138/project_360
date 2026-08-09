from html import escape
import traceback

from aiogram import types, Bot

from modules import mysql_adapter as sql
from modules import botdebug as d
import config

async def inline_query(inline_query: types.InlineQuery, bot: Bot):
    try:
        query = inline_query.query.split()

        if query[0] == "whisper":
            if len(query) < 3:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="⚠️ Недостаточно аргументов",
                    input_message_content=types.InputTextMessageContent(
                        message_text="""
Аргументы: whisper id_или_username сообщение
"""
                    ),
                    description="""
Аргументы: whisper id_или_username сообщение
"""
                )
                await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                return True

            userid = None
            username = None

            if query[1][0] != "@":
                try:
                    userid = int(query[1])
                except ValueError:
                    result = types.InlineQueryResultArticle(
                        id="1",
                        title="⚠️ Введите id или username пользователя",
                        input_message_content=types.InputTextMessageContent(
                            message_text="""
Аргументы: whisper id_или_username сообщение
"""
                        ),
                        description="""
Аргументы: whisper id_или_username сообщение
"""
                    )
                    await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                    return True
            else:
                if len(query[1]) < 3:
                    result = types.InlineQueryResultArticle(
                        id="1",
                        title="⚠️ Слишком короткий username",
                        input_message_content=types.InputTextMessageContent(
                            message_text="""
Аргументы: whisper id_или_username сообщение
"""
                        ),
                        description="""
Аргументы: whisper id_или_username сообщение
"""
                    )
                    await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                    return True
                username = query[1]

            n = await sql.add_whisper(userid or username, " ".join(query[2:]))

            markup = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="🔐 Просмотреть сообщение",
                            callback_data=f"whisper:{inline_query.from_user.id}:{n}",
                            style="primary"
                        )
                    ]
                ]
            )

            if userid:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="✉️ Отправить",
                    input_message_content=types.InputTextMessageContent(message_text=f"🔒 Скрытое сообщение для пользователя с id {userid}"),
                    reply_markup=markup
                )
            else:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="✉️ Отправить",
                    input_message_content=types.InputTextMessageContent(message_text=f"🔒 Скрытое сообщение для {username}"),
                    reply_markup=markup
                )

        elif query[0] == "anti-whisper":
            if len(query) < 3:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="⚠️ Недостаточно аргументов",
                    input_message_content=types.InputTextMessageContent(
                        message_text="""
Аргументы: anti-whisper id_или_username сообщение
"""
                    ),
                    description="""
Аргументы: anti-whisper id_или_username сообщение
"""
                )
                await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                return True

            userid = None
            username = None

            if query[1][0] != "@":
                try:
                    userid = int(query[1])
                except ValueError:
                    result = types.InlineQueryResultArticle(
                        id="1",
                        title="⚠️ Введите id или username пользователя",
                        input_message_content=types.InputTextMessageContent(
                            message_text="""
Аргументы: anti-whisper id_или_username сообщение
"""
                        ),
                        description="""
Аргументы: anti-whisper id_или_username сообщение
"""
                    )
                    await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                    return True
            else:
                if len(query[1]) < 3:
                    result = types.InlineQueryResultArticle(
                        id="1",
                        title="⚠️ Слишком короткий username",
                        input_message_content=types.InputTextMessageContent(
                            message_text="""
Аргументы: anti-whisper id_или_username сообщение"""
                        ),
                        description="""
Аргументы: anti-whisper id_или_username сообщение"""
                    )
                    await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                    return
                username = query[1]

            n = await sql.add_whisper(userid or username, " ".join(query[2:]))

            markup = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="🔐 Просмотреть сообщение",
                            callback_data=f"anti-whisper:{inline_query.from_user.id}:{n}",
                            style="primary"
                        )
                    ]
                ]
            )

            if userid:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="✉️ Отправить",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"🔒 Скрытое сообщение для всех кроме пользователя с id {userid}"
                    ),
                    reply_markup=markup
                )
            else:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="✉️ Отправить",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"🔒 Скрытое сообщение для всех кроме {username}"
                    ),
                    reply_markup=markup
                )
        else:
            return False

        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
        return True
    except:
        result = types.InlineQueryResultArticle(
            id="1",
            title="⚠️ Произошла ошибка, попробуйте позже",
            input_message_content=types.InputTextMessageContent(
                message_text="⚠️ Произошла ошибка, попробуйте позже"
            ),
        )
        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
        await bot.send_message(
            config.DEV_ADMIN_USERID,
            f"⚠️ Ошибка в inline_query. \
Traceback: \
<pre>{escape(traceback.format_exc()[-1000:])}</pre>",
            parse_mode='HTML'
        )
        return False

async def callback_query(call: types.CallbackQuery, bot: Bot):
    try:
        if call.data.startswith("whisper"):
            _, user, dbid = call.data.split(":")
            data = await sql.get_whisper(dbid)

            if data == ():
                await call.answer("⚠️ Данное сообщение не найдено. \
Возможно, сообщение было удалено", show_alert=True)
                return

            if (data[2] != str(call.from_user.id) and data[2] != f"@{call.from_user.username}") and \
                (user != str(call.from_user.id)):
                await call.answer("⚠️ Это не тебе", show_alert=True)
                return

            await call.answer(data[3][:200], show_alert=True)
        elif call.data.startswith("anti-whisper"):
            _, user, dbid = call.data.split(":")
            data = await sql.get_whisper(dbid)

            if data == ():
                await call.answer("⚠️ Данное сообщение не найдено. \
Возможно, сообщение было удалено", show_alert=True)
                return

            if data[2] == str(call.from_user.id) or data[2] == f"@{call.from_user.username}" and \
                (user != str(call.from_user.id)):
                await call.answer("⚠️ Это не тебе", show_alert=True)
                return

            await call.answer(data[3][:200], show_alert=True)
    except:
        await call.answer("⚠️ Произошла ошибка, попробуйте позже", show_alert=True)
        await d.send_view_traceback(call.message, traceback.format_exc(), bot, func="callback_query")
