"""Различные фильтры и декораторы для команд"""

import asyncio
import time
from collections import defaultdict
from functools import wraps

import config
from modules import async_tasks
from modules import utils

cooldown_list = defaultdict(lambda: defaultdict(float))


def cooldown(func=None, *, ctime=3):
    """Декоратор для ограничения частоты вызова команд (в секундах)"""
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            message = kwargs.get('message') or (args[0] if args else None)
            bot = kwargs.get('bot') or (args[1] if len(args) > 1 else None)

            if not message or not bot:
                raise ValueError("Message или Bot не найден в аргументах!")

            if not message.text:
                return await f(*args, **kwargs)

            command = message.text.split(maxsplit=1)[0]
            chat_id = message.chat.id
            command_last_used = cooldown_list[command][chat_id]
            current_time = time.time()

            if command_last_used + ctime < current_time:
                cooldown_list[command][chat_id] = current_time
            else:
                remaining = (command_last_used + ctime) - current_time
                msg = await message.reply(
                    f"<tg-emoji emoji-id=\"5240106125436683458\">⏳</tg-emoji> "
                    f"Подождите ещё {remaining:.2f} секунд",
                    parse_mode="HTML"
                )
                asyncio.create_task(async_tasks.delete_msg(msg, bot))
                asyncio.create_task(async_tasks.delete_msg(message, bot))
                return None

            return await f(*args, **kwargs)

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator


def only_groups(func):
    """Декоратор для команд и обработчиков. Разрешает выполнение только в группах/супергруппах"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if not message:
            raise ValueError("Message не найден в аргументах!")

        if message.chat.type not in ("supergroup", "group"):
            if message.text and message.text.startswith("/"):
                await message.reply("⚠️ Эта команда доступна только в группах/супергруппах")
            return None

        return await func(*args, **kwargs)

    return wrapper


def no_groups(func):
    """Декоратор для команд. Запрещает обычные группы (требует супергруппу)"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if not message:
            raise ValueError("Message не найден в аргументах!")

        if message.chat.type == "group":
            await message.reply("⚠️ Эта команда доступна только в супергруппах")
            return None

        return await func(*args, **kwargs)

    return wrapper


def only_private(func):
    """Декоратор для команд. Разрешает выполнение только в личных сообщениях"""
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


def only_sentry_instance(func):
    """Фильтр для команд, доступных только на определенном инстансе бота"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get('message') or (args[0] if args else None)

        if utils.BOT_ID != 7732881719 and utils.BOT_ID != 0:
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

        if (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.id == config.DEV_ADMIN_USERID
        ):
            await message.reply("⚠️ Нельзя использовать эту команду на разработчике")
            return None

        return await func(*args, **kwargs)

    return wrapper
