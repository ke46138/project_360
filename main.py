#!/usr/bin/python3
"""Главный модуль бота"""

import config
config.reload()
from modules.logger import logger

logger.info("Загрузка включённых модулей...")
logger.info("[1/4] Загрузка встроенных библиотек...")

import asyncio

logger.info("[2/4] Загрузка оверлеев...")

from overlays import random

logger.info("[3/4] Загрузка внешних библиотек...")

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.filters import CommandStart, Command
from aiogram import Bot, Dispatcher
from aiogram import types

# from aiogram_prometheus import PrometheusUpdatesMiddleware, PrometheusWrapperStorage
# from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

logger.info("[4/4] Загрузка модулей...")

from modules import admin_arbuz
from modules import auth
from modules import beer
from modules import botdebug
from modules import ban
from modules import clear_tasks
from modules import chat_management
from modules import dr_dialog
from modules import entertainment
from modules import filters
from modules import mute
from modules import sudo
from modules import tags
from modules import themes
from modules import mysql_adapter as sql
from modules import profiles
from modules import redis
from modules import report
from modules import reputation
from modules import rp_commands
from modules import userdb
from modules import utils
from modules import message_router
from modules import iris_bindings

logger.info("Все модули загружены")

session = AiohttpSession(
    api=TelegramAPIServer.from_base(
        config.BOT_API_SERVER if config.CUSTOM_BOT_API_ENABLED else "https://api.telegram.org"
    ),
    limit=20
)
properties = DefaultBotProperties(parse_mode="HTML")

bot = Bot(token=config.BOT_TOKEN, session=session, default=properties)
#dp = Dispatcher(storage=PrometheusWrapperStorage(MemoryStorage()))
dp = Dispatcher(
    storage = RedisStorage.from_url(
        utils.build_redis_url(
            config.REDIS_HOST,
            config.REDIS_PORT,
            config.REDIS_PASSWORD,
            config.REDIS_DATABASE,
            config.REDIS_USER
        )
    )
)

#dp.update.middleware(PrometheusUpdatesMiddleware())
dp.message.middleware(botdebug.ExecutionTimeMiddleware())
bot.session.middleware(themes.ThemeMiddleware())

logger.info("Настраиваются роутеры")

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
dp.include_router(tags.router)
dp.include_router(iris_bindings.router)
dp.include_router(message_router.router)

logger.info("Роутеры настроены")

if config.API_MODE == "webhook":
    global app

    import traceback

    from contextlib import asynccontextmanager
    from fastapi import FastAPI, Request, Response

    @asynccontextmanager
    async def lifespan(app1: FastAPI):
        """Lifespan для автоматического удаления и установки вебхука"""
        logger.info("Запуск FastAPI")
        await redis.init()
        await sql.init()
        await utils.set_bot_id(bot)
        await bot.set_my_commands(
            commands=[
                types.BotCommand(command="start", description="Показать приветствие"),
                types.BotCommand(command="help_beta", description="Показать справку"),
                types.BotCommand(command="about", description="О боте")
            ],
            scope=types.BotCommandScopeAllPrivateChats()
        )
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
        logger.info("Завершение работы...")
        remove_left_task.cancel()
        await sql.close()
        await bot.delete_webhook()
        logger.info("Вебхук удалён")

    app = FastAPI(lifespan=lifespan)

    async def process_update(update):
        """Asyncio задача для парсинга обновлений"""
        try:
            await dp.feed_update(bot, update)
        except:
            logger.error(traceback.format_exc())
            await bot.send_message(
                config.DEV_ADMIN_USERID,
                f"""⚠️ Произошла ошибка при обработке обновления
    Traceback:
    <pre>
    {traceback.format_exc()[-1000:]}
    </pre>""",
                parse_mode="HTML"
            )

    @app.post(config.WEBHOOK_URL)
    async def webhook_handler(request: Request):
        """Хандлер вебхуков"""
        data = await request.json()
        update = types.Update.model_validate(data)

        asyncio.create_task(process_update(update))

        return {"ok": True}

async def polling_startup():
    await redis.init()
    await sql.init()
    await utils.set_bot_id(bot)
    await bot.set_my_commands(
        commands=[
            types.BotCommand(command="start", description="Показать приветствие"),
            types.BotCommand(command="help_beta", description="Показать справку"),
            types.BotCommand(command="about", description="О боте")
        ],
        scope=types.BotCommandScopeAllPrivateChats()
    )
    remove_left_task = asyncio.create_task(
        clear_tasks.periodic_task(
            clear_tasks.remove_left_task,
            bot,
            delay_start=360,
            interval=18000,
        )
    )
    await dp.start_polling(bot)
    remove_left_task.cancel()
    await sql.close()

# @app.get("/metrics")
# async def metrics():
#     """Возвращает метрики в формате Prometheus"""
#     return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@dp.message(CommandStart())
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
                    url=f"https://telegram.me/{utils.BOT_USERNAME}?startgroup=true"
                )
            ]
        ]
    )

    await message.reply(
"Привет! Это бот для администрирования групп. \
Просто добавь его в группу. \
Частичный список команд можно посмотреть по команде /help_beta",
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=markup
    )

@dp.message(Command("rules"))
@botdebug.bugreport
@filters.cooldown
@filters.only_groups
async def rules_command(message: types.Message, bot: Bot):
    """Команда /rules для отправки правил"""
    await message.reply(await sql.get_group_rules(message.chat.id), parse_mode='HTML')

@dp.message(Command("ping"))
@botdebug.bugreport
@filters.cooldown
async def ping_command(message: types.Message, bot: Bot):
    """Команда для теста доступности бота"""
    await message.reply("Pong!")

@dp.message(Command("about"))
@botdebug.bugreport
@filters.cooldown
async def about_command(message: types.Message, bot: Bot):
    """Команда для вывода информации о боте"""
    await message.reply(config.ABOUT_BOT_TEXT, parse_mode='HTML')

@dp.message(Command("reload_config"))
@botdebug.bugreport
@filters.cooldown
@auth.require_auth
async def reload_config_command(message: types.Message, bot: Bot):
    """Перезагружает конфиг по команде /reload_config"""
    config.reload()
    await message.react([types.ReactionTypeEmoji(emoji='👍')])

@dp.message(Command("get_user_id"))
@botdebug.bugreport
@filters.cooldown
async def get_user_id_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        if message.reply_to_message.forward_origin:
            if isinstance(message.reply_to_message.forward_origin, types.MessageOriginHiddenUser):
                await message.answer(
                    f"⚠️ У пересланного сообщения скрыт аккаунт, получить user_id невозможно"
                )
            if isinstance(message.reply_to_message.forward_origin, types.MessageOriginUser):
                await message.reply(f"{message.reply_to_message.forward_origin.sender_user.id}")
        else:
            await message.reply(f"{message.reply_to_message.from_user.id}")
    else:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя (можно пересланное), \
чей user_id вы хотите узнать"
        )

if __name__ == "__main__":
    from sdnotify import SystemdNotifier
    notifier = SystemdNotifier()
    notifier.notify('READY=1')

    if config.API_MODE == "polling":
        asyncio.run(polling_startup())
    elif config.API_MODE == "webhook":
        import uvicorn
        uvicorn.run(app, host=config.HOST, port=config.PORT, access_log=False)
