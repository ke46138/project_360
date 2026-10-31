#!/usr/bin/env python3
"""Главный модуль"""

from __future__ import annotations

import asyncio
import traceback

import config
from modules.logger import logger

from overlays import random # noqa: F401

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.redis import RedisStorage

from modules import admin_arbuz
from modules import auth
from modules import awards
from modules import ban
from modules import beer
from modules import botdebug
from modules import chat_management
from modules import clear_tasks
from modules import dr_dialog
from modules import entertainment
from modules import filters
from modules import iris_bindings
from modules import message_router
from modules import mute
from modules import mysql_adapter as sql
from modules import profiles
from modules import redis
from modules import report
from modules import reputation
from modules import rp_commands
from modules import sudo
from modules import tags
from modules import themes
from modules import userdb
from modules import utils

session = AiohttpSession(
    api=TelegramAPIServer.from_base(
        config.BOT_API_SERVER if config.CUSTOM_BOT_API_ENABLED else "https://api.telegram.org"
    ),
    limit=20,
)
properties = DefaultBotProperties(parse_mode="HTML")
bot = Bot(token=config.BOT_TOKEN, session=session, default=properties)

storage = RedisStorage.from_url(
    utils.build_redis_url(
        config.REDIS_HOST,
        config.REDIS_PORT,
        config.REDIS_PASSWORD,
        config.REDIS_DATABASE,
        config.REDIS_USER,
    )
)
dp = Dispatcher(storage=storage)

dp.message.middleware(botdebug.ExecutionTimeMiddleware())
bot.session.middleware(themes.ThemeMiddleware())

router = Router()


@router.message(CommandStart())
@botdebug.bugreport
@filters.cooldown
@filters.only_private
async def start_command(message: types.Message, bot: Bot):
    """Команда /start"""
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Добавить в группу",
                    url=f"https://telegram.me/{utils.BOT_USERNAME}?startgroup=true",
                )
            ]
        ]
    )

    await message.reply(
        "Привет! Это бот для администрирования групп. "
        "Просто добавь его в группу. "
        "Частичный список команд можно посмотреть по команде /help_beta",
        parse_mode="HTML",
        link_preview_options=types.LinkPreviewOptions(is_disabled=True),
        reply_markup=markup,
    )


@router.message(Command("rules"))
@botdebug.bugreport
@filters.cooldown
@filters.only_groups
async def rules_command(message: types.Message, bot: Bot):
    """Команда /rules для отправки правил группы."""
    rules = await sql.get_group_rules(message.chat.id)
    await message.reply(rules, parse_mode="HTML")


@router.message(Command("ping"))
@botdebug.bugreport
@filters.cooldown
async def ping_command(message: types.Message, bot: Bot):
    """Команда для проверки доступности бота."""
    await message.reply("Pong!")


@router.message(Command("about"))
@botdebug.bugreport
@filters.cooldown
async def about_command(message: types.Message, bot: Bot):
    """Команда для вывода информации о боте."""
    await message.reply(config.ABOUT_BOT_TEXT, parse_mode="HTML")


@router.message(Command("reload_config"))
@botdebug.bugreport
@filters.cooldown
@auth.require_auth
async def reload_config_command(message: types.Message, bot: Bot):
    """Перезагружает конфигурацию из .env и переменных окружения"""
    config.reload()
    await message.react([types.ReactionTypeEmoji(emoji="👍")])


@router.message(Command("get_user_id"))
@botdebug.bugreport
@filters.cooldown
async def get_user_id_command(message: types.Message, bot: Bot):
    """Команда для получения Telegram user_id."""
    if not message.reply_to_message:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя (можно пересланное), чей user_id вы хотите узнать"
        )
        return

    reply = message.reply_to_message
    if reply.forward_origin:
        if isinstance(reply.forward_origin, types.MessageOriginHiddenUser):
            await message.answer("⚠️ У пересланного сообщения скрыт аккаунт, получить user_id невозможно")
            return
        if isinstance(reply.forward_origin, types.MessageOriginUser):
            await message.reply(f"{reply.forward_origin.sender_user.id}")
            return

    if reply.from_user:
        await message.reply(f"{reply.from_user.id}")
    else:
        await message.reply("⚠️ Не удалось определить отправителя")


dp.include_router(router)
dp.include_router(mute.router)
dp.include_router(report.router)
dp.include_router(botdebug.router)
dp.include_router(dr_dialog.router)
dp.include_router(ban.router)
dp.include_router(sudo.router)
dp.include_router(userdb.router)
dp.include_router(beer.router)
dp.include_router(reputation.router)
dp.include_router(rp_commands.router)
dp.include_router(themes.router)
dp.include_router(admin_arbuz.router)
dp.include_router(entertainment.router)
dp.include_router(chat_management.router)
dp.include_router(profiles.router)
dp.include_router(awards.router)
dp.include_router(tags.router)
dp.include_router(iris_bindings.router)
dp.include_router(message_router.router)


async def setup_bot():
    """Общая инициализация ресурсов бота."""
    logger.info("Инициализация сервисов...")
    await redis.init()
    await sql.init()
    await utils.set_bot_id(bot)
    await bot.set_my_commands(
        commands=[
            types.BotCommand(command="start", description="Показать приветствие"),
            types.BotCommand(command="help_beta", description="Показать справку"),
            types.BotCommand(command="about", description="О боте"),
        ],
        scope=types.BotCommandScopeAllPrivateChats(),
    )
    logger.info("Бот готов к работе под именем @%s (ID: %s)", utils.BOT_USERNAME, utils.BOT_ID)


async def cleanup_bot():
    """Освобождение всех занятых ресурсов"""
    logger.info("Завершение работы и освобождение ресурсов...")
    try:
        await sql.close()
    except Exception:
        logger.exception("Ошибка при закрытии MySQL пула")

    try:
        await bot.session.close()
    except Exception:
        logger.exception("Ошибка при закрытии сессии бота")
    logger.info("Ресурсы успешно освобождены")


async def polling_startup():
    """Запуск бота в режиме polling"""
    await setup_bot()
    remove_left_task = asyncio.create_task(
        clear_tasks.periodic_task(
            clear_tasks.remove_left_task,
            bot,
            delay_start=360,
            interval=18000,
        )
    )

    try:
        logger.info("Запуск в режиме polling...")
        await dp.start_polling(bot)
    finally:
        remove_left_task.cancel()
        await cleanup_bot()


app = None
if config.API_MODE == "webhook":
    from contextlib import asynccontextmanager
    from fastapi import FastAPI, Request

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI):
        logger.info("Запуск FastAPI")
        await setup_bot()
        await bot.delete_webhook()
        logger.info("Вебхук удалён")
        await bot.set_webhook(config.WEBHOOK_URL_FULL)
        logger.info("Вебхук установлен")
        remove_left_task = asyncio.create_task(
            clear_tasks.periodic_task(
                clear_tasks.remove_left_task,
                bot,
                delay_start=360,
                interval=18000,
            )
        )
        yield

        remove_left_task.cancel()
        try:
            await bot.delete_webhook()
        except Exception:
            pass
        await cleanup_bot()

    app = FastAPI(lifespan=lifespan)

    async def process_update(update: types.Update):
        try:
            await dp.feed_update(bot, update)
        except Exception:
            logger.error(traceback.format_exc())
            if config.DEV_ADMIN_USERID:
                try:
                    await bot.send_message(
                        config.DEV_ADMIN_USERID,
                        f"⚠️ Произошла ошибка при обработке обновления\n"
                        f"Traceback:\n<pre>{traceback.format_exc()[-1000:]}</pre>",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

    @app.post(config.WEBHOOK_URL)
    async def webhook_handler(request: Request):
        data = await request.json()
        update = types.Update.model_validate(data)
        asyncio.create_task(process_update(update))
        return {"ok": True}


if __name__ == "__main__":
    if config.API_MODE == "polling":
        try:
            asyncio.run(polling_startup())
        except (KeyboardInterrupt, SystemExit):
            logger.info("Бот остановлен пользователем.")
    elif config.API_MODE == "webhook":
        import uvicorn
        logger.info("Запуск HTTP сервера uvicorn на %s:%s", config.HOST, config.PORT)
        uvicorn.run(app, host=config.HOST, port=config.PORT, access_log=False)
    else:
        logger.error("Неизвестный API_MODE: '%s'. Доступны: polling, webhook", config.API_MODE)
