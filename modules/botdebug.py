"""Модуль для дебага бота"""

from typing import Callable, Awaitable
from functools import wraps
from html import escape
import asyncio
import traceback
import random
import string
import time

from aiogram import Router, types, Bot, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, TelegramObject

from modules import auth
from modules import mysql_adapter as sql
from modules import filters
from modules import redis
from modules.logger import logger
from modules import utils

import config

router = Router()
last_tb = "NO_TRACEBACK"

deleteMarkup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Удалить сообщение",
                callback_data="deletemessage"
            )
        ]
    ]
)

async def send_view_traceback(message: types.Message, tb: str, bot: Bot, func="none"):
    logger.error(tb)

    global last_tb

    markup = InlineKeyboardMarkup(
            inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="tracebackyes"),
                InlineKeyboardButton(text="Нет", callback_data="tracebackno")
            ]
        ]
    )

    last_tb = tb.replace(config.BOT_PATH, "*СТЁРТО*")
    error_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))

    if message:
        if message.from_user.id == utils.BOT_ID:
            await message.edit_text(
                f"⚠️ Произошла ошибка при выполнении операции. \
Багрепорт будет отправлен разработчику. GasterID: {error_id}. \
Желаете посмотреть последний traceback?",
                reply_markup=markup
        )
        else:
            await message.reply(
                f"⚠️ Произошла ошибка при выполнении операции. \
Багрепорт будет отправлен разработчику. GasterID: {error_id}. \
Желаете посмотреть последний traceback?",
                reply_markup=markup
            )

    await bot.send_message(
        config.DEV_ADMIN_USERID,
        f"""⚠️ Произошла ошибка при выполнении операции.
Функция: {func}
GasterID: {error_id}
Traceback:
<pre>{escape(last_tb[-1000:])}</pre>""",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@router.message(Command('debug'))
@auth.require_auth
async def debug(message: types.Message, bot: Bot):
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Белый список доменов", callback_data="urlallowlist")],
                [InlineKeyboardButton(text="Удалить сообщение", callback_data="deletemessage")]
            ]
        )

        await message.reply("Что вы хотите отладить?", reply_markup=markup)
    except:
        await send_view_traceback(message, traceback.format_exc(), bot)

def bugreport(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)
        bot = kwargs.get('bot') or (args[1] if args else None)

        if not message or not bot:
            raise ValueError("Message или Bot не найден в аргументах!")

        try:
            return await func(*args, **kwargs)
        except:
            await send_view_traceback(message, traceback.format_exc(), bot, func.__name__)

    return wrapper

@router.message(Command('levelcheck'))
@auth.require_auth(level=999)
@bugreport
async def levelcheck_command(message: types.Message, bot: Bot):
    await message.reply("Такого не бывает")

@router.message(Command('manual_exception'))
@auth.require_auth
@bugreport
async def manual_exception(message: types.Message, bot: Bot):
    raise Exception("TEST. IGNORE THIS")

@router.message(Command('show_flow_speed'))
@bugreport
async def show_flow_speed_command(message: types.Message, bot: Bot):
    """Команда для показа скорости потока сообщений"""
    result = await sql.get_msg_flow()

    await message.reply(
        f"📊 Общий поток сообщений:\n"
        f"В секунду: {result[0]}\n"
        f"В минуту: {result[1]}\n"
        f"В час: {result[2]}\n"
        f"В день: {result[3]}"
    )

@router.message(Command("send_emoji"))
@bugreport
@auth.require_auth
async def send_custom_emoji(message: types.Message):
    await message.reply(
        f"<tg-emoji emoji-id='5260368840541358565'>😏</tg-emoji>",
        parse_mode="HTML"
    )

@router.message(Command("get_emoji"))
@bugreport
async def get_emoji_command(message: types.Message):
    if not message.entities:
        await message.reply("🚫 В сообщении отсутствуют премиум эмодзи")
        return

    for entity in message.entities:
        if entity.type == "custom_emoji":
            await message.reply(f"custom_emoji_id: {entity.custom_emoji_id}")

@router.message(Command("cooldown_test"))
@bugreport
@filters.cooldown(ctime=10)
async def cooldown_test_command(message: types.Message, bot: Bot):
    await message.reply("Работает")

@router.message(Command("wrap_user_link_test"))
@bugreport
async def wrap_user_link_test_command(message: types.Message, bot: Bot):
    await message.reply(utils.wrap_user_link(message.from_user.full_name, message.from_user.id), parse_mode="HTML")

@router.message(Command("test_stream"))
@bugreport
async def test_stream_command(message: types.Message, bot: Bot):
    test_text = "Это тест стриминга как в чатгпт"
    temp = ""

    for i in test_text:
        temp += i
        await bot.send_message_draft(message.chat.id, 1, text=temp)
        await asyncio.sleep(0.2)

    await message.reply(temp)

@router.message(Command("redis_set_dsmsgid"))
@bugreport
@auth.require_auth
async def test_redis_set_dsmsgid_command(message: types.Message, bot: Bot):
    args = message.text.split()

    if len(args) <= 1:
        await message.reply("⚠️ Недостаточно аргументов")
        return

    try:
        value = int(args[1])
    except ValueError:
        await message.reply("⚠️ Первый аргумент должен быть числом")
        return

    await redis.set_deepseek_message_id(value)

    await message.react([types.ReactionTypeEmoji(emoji='👍')])

@router.message(Command("redis_incr_key"))
@bugreport
@auth.require_auth
async def test_redis_incr_key_command(message: types.Message, bot: Bot):
    args = message.text.split()

    if len(args) <= 1:
        await message.reply("⚠️ Недостаточно аргументов")
        return

    result = await redis.incr_key(args[1])

    await message.reply(f"Текущее значение: {result}")

@router.message(Command("redis_get_dsmsgid"))
@bugreport
@auth.require_auth
async def test_redis_get_dsmsgid_command(message: types.Message, bot: Bot):
    result = await redis.get_deepseek_message_id()

    await message.reply(f"Значение в redis: {result}")

@router.message(Command("help_beta"))
@bugreport
@filters.cooldown
@filters.only_private
async def start_handler(message: types.Message, bot: Bot) -> None:
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Справка",
                    web_app=types.WebAppInfo(
                        url="https://ke46138.ddns.net/docs/project_360/commands.html"
                    )
                )
            ]
        ]
    )

    await message.answer(
        text="Нажмите на кнопку ниже, чтобы открыть справку",
        reply_markup=keyboard
    )

async def callback_query(call: types.CallbackQuery):
    if call.data == 'urlallowlist':
        await call.message.edit_text(str(config.URL_ALLOWLIST), reply_markup=deleteMarkup)
    elif call.data == 'tracebackyes':
        await call.message.edit_text(
            f"<pre>{escape(last_tb[-1000:])}</pre>",
            reply_markup=deleteMarkup,
            disable_web_page_preview=True,
            parse_mode="HTML"
        )
    elif call.data == 'tracebackno':
        await call.message.delete()
    elif call.data == 'deletemessage':
        await call.message.delete()
    else:
        return
    await call.answer("Готово!")

class ExecutionTimeMiddleware(BaseMiddleware):
    """Middleware для измерения скорости выполнения хандлеров"""
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[None]],
        event: TelegramObject,
        data: dict
    ) -> None:
        try:
            start_time = time.perf_counter()
            await handler(event, data)
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000

            user = data.get("event_from_user")
            if isinstance(event, types.Message):
                chatid = event.chat.id
            elif isinstance(event, types.CallbackQuery):
                chatid = event.message.chat.id
            else:
                chatid = 0

            command = getattr(event, "text", "unknown")

            if command is None or command[0] != "/":
                command = "srv"
            if command != "/show_performance":
                await sql.write_statistics(command[:30], duration, getattr(user, 'id', 0), chatid)
        except:
            logger.error(traceback.format_exc())
