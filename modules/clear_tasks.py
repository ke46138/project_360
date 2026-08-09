import asyncio
import inspect

from aiogram import Bot

from modules import mysql_adapter as sql
from modules.logger import logger

async def remove_left_task(bot: Bot):
    logger.info("Начинается чистка базы данных пользователей от мусора")
    users = await sql.get_all_group_users()
    for i in users:
        try:
            user = await bot.get_chat_member(i[1], i[0])
            if user.status == "left" or user.status == "kicked":
                logger.info(f"Пользователь с userid {i[0]} и chatid {i[1]} не найден и удалён")
                await sql.remove_user(i[0], i[1])
        except Exception as e:
            logger.info(f"Пользователь с userid {i[0]} и chatid {i[1]} выдал ошибку {e} и удалён")
            await sql.remove_user(i[0], i[1])
        await asyncio.sleep(0.4)
    logger.info("Чистка завершена")

async def periodic_task(func, *args, delay_start: int = 0, interval: int = 300, **kwargs):
    """
    Функция для периодического запуска любой функции.

    :param func: функция или корутина для выполнения
    :param delay_start: задержка перед первым запуском (секунды)
    :param interval: интервал между запусками (секунды)
    :param args: позиционные аргументы для функции
    :param kwargs: именованные аргументы для функции
    """
    logger.info(
        f"Создана отложенная задача {func.__name__}. \
Отложенный запуск: {delay_start} секунд, интервал: {interval} секунд"
    )
    await asyncio.sleep(delay_start)
    while True:
        if inspect.iscoroutinefunction(func):
            await func(*args, **kwargs)
        else:
            func(*args, **kwargs)
        await asyncio.sleep(interval)