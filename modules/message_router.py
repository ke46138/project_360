import traceback

from aiogram import Router, types, Bot

# from modules import antiflood
from modules import botdebug as d
from modules import entertainment
from modules import inline_rp
from modules import mute
from modules import userdb
from modules import helper
from modules import urlfilter
from modules import whisper
from modules import utils

router = Router()
HELP_TEXT = f"""
Запрос состоит из названия режима и его аргументов.
Пример: @{utils.BOT_USERNAME} mode something
mode - режим
something - аргументы режима

Доступные режимы:
- whisper
Отправить секретное сообщение по юзернейму или user_id. Принимает аргументы в формате @{utils.BOT_USERNAME} whisper @юзернейм текст сообщения.
Если у пользователя отсутсвует юзернейм, то командой /get_user_id можно получить его user_id.
- anti-whisper
Тоже самое что и whisper, но наоборот: сообщение не сможет посмотреть тот пользователь, которого вы указали.
- text2windings
Перевести английский текст в windings
- windings2text
Перевести текст на windings в обычный"""

@router.message()
async def msg_handler(message: types.Message, bot: Bot):
    await userdb.message_handler(message, bot)
    await urlfilter.filter_msg(message, bot)
    # await antiflood.message_handler(message, bot)

@router.inline_query()
async def inline_query(inline_query: types.InlineQuery, bot: Bot):
    if inline_query.query == "":
        result = types.InlineQueryResultArticle(
            id="1",
            title="ℹ️ Нажмите чтобы получить справку по inline режиму",
            input_message_content=types.InputTextMessageContent(
                message_text=HELP_TEXT
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
            title="⚠️ Неверный режим | ℹ️ Нажмите чтобы получить справку по inline режиму",
            input_message_content=types.InputTextMessageContent(
                message_text=HELP_TEXT
            )
        )
        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)

@router.callback_query()
async def callback_query(call: types.CallbackQuery, bot: Bot):
    try:
        await d.callback_query(call)
        await mute.callback_query(call, bot)
        await entertainment.callback_query(call, bot)
        await helper.cb_back_root(call, bot)
        await helper.cb_file(call, bot)
        await helper.cb_func(call, bot)
        await inline_rp.callback_query(call, bot)
        await whisper.callback_query(call, bot)
    except:
        await d.send_view_traceback(call.message, traceback.format_exc(), bot, func="callback_query")
