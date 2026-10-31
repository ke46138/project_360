"""Роутер общих сообщений, inline-запросов и callback-кнопок"""

import traceback

from aiogram import Router, types, Bot

from modules import antiflood
from modules import botdebug as d
from modules import entertainment
from modules import helper
from modules import inline_rp
from modules import mute
from modules import urlfilter
from modules import userdb
from modules import utils
from modules import whisper

router = Router()


def get_help_text() -> str:
    return f"""Запрос состоит из названия режима и его аргументов.
Пример: @{utils.BOT_USERNAME} mode something
mode - режим
something - аргументы режима

Доступные режимы:
- whisper
Отправить секретное сообщение по юзернейму или user_id. Принимает аргументы в формате @{utils.BOT_USERNAME} whisper @юзернейм текст сообщения.
Если у пользователя отсутствует юзернейм, то командой /get_user_id можно получить его user_id.
- anti-whisper
То же самое что и whisper, но наоборот: сообщение не сможет посмотреть тот пользователь, которого вы указали.
- text2windings
Перевести английский текст в windings
- windings2text
Перевести текст на windings в обычный"""


@router.message()
async def msg_handler(message: types.Message, bot: Bot):
    """Главный обработчик всех сообщений"""
    await userdb.message_handler(message, bot)
    await urlfilter.filter_msg(message, bot)
    await antiflood.message_handler(message, bot)


@router.inline_query()
async def inline_query(inline_query: types.InlineQuery, bot: Bot):
    """Обработчик inline запросов"""
    if not inline_query.query or inline_query.query.strip() == "":
        result = types.InlineQueryResultArticle(
            id="1",
            title="ℹ️ Нажмите, чтобы получить справку по inline режиму",
            input_message_content=types.InputTextMessageContent(
                message_text=get_help_text()
            )
        )
        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
        return

    res = (
        await whisper.inline_query(inline_query, bot),
        await inline_rp.inline_query(inline_query, bot)
    )

    if not any(res):
        result = types.InlineQueryResultArticle(
            id="1",
            title="⚠️ Неверный режим | ℹ️ Нажмите, чтобы получить справку по inline режиму",
            input_message_content=types.InputTextMessageContent(
                message_text=get_help_text()
            )
        )
        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)


@router.callback_query()
async def callback_query(call: types.CallbackQuery, bot: Bot):
    """Маршрутизатор нажатий inline кнопок"""
    data = call.data or ""
    try:
        if data in ('urlallowlist', 'tracebackyes', 'tracebackno', 'deletemessage'):
            await d.callback_query(call)
            return

        if data.startswith("unmute"):
            await mute.callback_query(call, bot)
            return

        if data.startswith(("accept_marriage", "deny_marriage", "cancel_marriage", "cubesyes", "cubesno", "game_")):
            await entertainment.callback_query(call, bot)
            return

        if data == "back:root":
            await helper.cb_back_root(call, bot)
            return
        if data.startswith("file:"):
            await helper.cb_file(call, bot)
            return
        if data.startswith("func:"):
            await helper.cb_func(call, bot)
            return

        if data.startswith(("snowgraveyes", "inlineno")):
            await inline_rp.callback_query(call, bot)
            return

        if data.startswith(("whisper", "anti-whisper")):
            await whisper.callback_query(call, bot)
            return

        await d.callback_query(call)
    except Exception:
        await d.send_view_traceback(call.message, traceback.format_exc(), bot, func="callback_query")
