"""Модуль для авторизации пользователей"""

from functools import wraps
import random

from aiogram import types, Bot

from modules import mysql_adapter as sql
import config

error_messages = [
    "⚠️ Команда недоступна. Попробуйте подкупить админа печеньками",
    "⚠️ У вас недостаточно прав. Но у вас есть право сделать чай!",
    "⚠️ Ошибка: эта команда для секретных агентов, а у вас нет галстука",
    "⚠️ Попытка отклонена. Бот решил, что вы слишком милы для этой команды",
    "⚠️ 360 сказал нет. Попробуйте уговорить его... чем-нибудь",
    "⚠️ Доступ запрещён. Но вы можете постоять здесь и полюбоваться красивой ошибкой",
    "⚠️ Команда спряталась от вас. Видимо, не хочет выполняться",
    "⚠️ Команда недоступна. Попробуйте подкупить админа артом или тг звёздами",
    "⚠️ Аксес денайд! Уровень допуска ниже плинтуса",
    "⚠️ Даже пингвины знают - у вас нет прав на это",
    "⚠️ Хотите выполнить команду? Отлично. Разрешение покажете? У вас его нет? Тогда нельзя",
    "⚠️ В доступе отказано. Попробуйте купить DLC \"Права администратора\"",
    "⚠️ Нельзя! Вы ещё не прокачали навык \"Великий администратор\"",
    "⚠️ Команда активна только при наличии прав. А их... нет"
]

async def authorize(message: types.Message, bot: Bot, level=255):
    """Функция авторизации пользователей для использования админских функций.
    Не обрабатывает исключения.
    Возвращает:
    -1 - неопределён userid (это вообще может произойти?)
    1 - всё ок
    0 - доступ запрещён"""
    if message.sender_chat:
        user_id = message.sender_chat.id
    elif message.from_user:
        user_id = message.from_user.id
    else:
        return -1

    if message.chat.type == "private":
        if user_id not in config.DEVS:
            return 0
        else:
            pass
    else:
        if user_id == message.chat.id and level <= 200:
            return 1

        admins = await sql.get_group_admins(message.chat.id, bot)

        if admins:
            pattern = [user_id]
            result = next(
                (item for item in admins if item[:len(pattern)] == pattern),
                None
            )

            if result is None:
                return 0

            if result[1] < level:
                return 0
        else:
            return 0

    return 1

async def authorize_callback_query(call: types.CallbackQuery, bot: Bot, level=255):
    userid = call.from_user.id

    if not call.message:
        return 0

    if call.message.chat.type == "private":
        if userid not in config.DEVS:
            return 0
        else:
            return 1
    else:
        admins = await sql.get_group_admins(call.message.chat.id, bot)

        if admins:
            pattern = [userid]
            result = next(
                (item for item in admins if item[:len(pattern)] == pattern),
                None
            )

            if result is None:
                return 0

            if result[1] < level:
                return 0
            else:
                return 1
        else:
            return 0

    return 0

def randomise_errors():
    return random.choice(error_messages)

def require_auth(func=None, *, level=255):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            message = kwargs.get('message') or (args[0] if args else None)
            bot = kwargs.get('bot') or (args[1] if args else None)

            if not message:
                raise ValueError("Message не найден в аргументах!")

            if not bot:
                raise ValueError("Bot не найден в аргументах!")

            if await authorize(message, bot, level=level) != 1:
                await message.reply(randomise_errors())
                return None

            return await f(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator
