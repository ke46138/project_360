"""Различные фильтры для команд"""

import asyncio
import time
from collections import defaultdict
from functools import wraps

import config
from modules import async_tasks
from modules import utils

cooldown_list = defaultdict(lambda: defaultdict(float))

def cooldown(func=None, *, ctime=3):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            message = kwargs.get('message') or (args[0] if args else None)
            bot = kwargs.get('bot') or (args[1] if args else None)

            if not message or not bot:
                raise ValueError("Message или Bot не найден в аргументах!")

            command, *_ = message.text.split(maxsplit=1)
            command_last_used = cooldown_list[command][message.chat.id]

            temp_time = time.time()

            if command_last_used + ctime < temp_time:
                cooldown_list[command][message.chat.id] = temp_time
            else:
                msg = await message.reply(
                    f"<tg-emoji emoji-id=\"5240106125436683458\">⏳</tg-emoji> Подождите ещё {((command_last_used + ctime) - temp_time):.2f} секунд",
                    parse_mode="HTML"
                )
                await asyncio.create_task(async_tasks.delete_msg(msg, bot))
                await asyncio.create_task(async_tasks.delete_msg(message, bot))
                return None

            return await f(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator

def only_groups(func):
    """Декоратор для команд. Запрещает команду везде, кроме групп"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if not message:
            raise ValueError("Message не найден в аргументах!")

        if message.chat.type != "supergroup" and message.chat.type != "group":
            await message.reply("⚠️ Эта команда доступна только в группах/супергруппах")
            return None

        return await func(*args, **kwargs)

    return wrapper

def no_groups(func):
    """Декоратор для команд. Запрещает команду в группах"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if not message:
            raise ValueError("Message не найден в аргументах!")

        if message.chat.type == "group":
            await message.reply("⚠️ Эта команда доступна только в супергруппах/группах")
            return None

        return await func(*args, **kwargs)

    return wrapper

def only_private(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if not message:
            raise ValueError("Message не найден в аргументах!")

        if message.chat.type != "private":
            await message.reply("⚠️ Эта команда доступна только в личных сообщениях")
            return None

        return await func(*args, **kwargs)

    return wrapper

def not_for_abrikos(func=None, *, detect=True):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            message = kwargs.get('message') or (args[0] if args else None)

            if not message:
                raise ValueError("Message не найден в аргументах!")

            if message.chat.id == -1002298339941:
                if not detect:
                    return None
                await message.reply("⚠️ Эта команда недоступна в группе абрикоса")
                return None

            return await f(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator

def only_abrikos(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if not message:
            raise ValueError("Message не найден в аргументах!")

        if message.chat.id != -1002298339941:
            await message.reply("⚠️ Эта команда работает только в группе абрикоса")
            return

        return await func(*args, **kwargs)

    return wrapper

def only_sentry_instance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if utils.BOT_ID != 7732881719:
            await message.reply("⚠️ Эта команда доступна только у бота 360 Total Security | Sentry")
            return None

        return await func(*args, **kwargs)

    return wrapper

def antidev(func):
    """Декоратор для команд. Запрещает использовать команду на разработчике"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if not message:
            raise ValueError("Message не найден в аргументах!")

        if message.reply_to_message and message.reply_to_message.from_user.id == config.DEV_ADMIN_USERID:
            await message.reply("⚠️ Нельзя использовать эту команду на разработчике")
            return

        return await func(*args, **kwargs)

    return wrapper
