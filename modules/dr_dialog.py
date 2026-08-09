"""Модуль для создания диалогов в стиле Deltarune"""

import os
import sys
import random
import asyncio

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import filters
from modules import botdebug as d
from modules.logger import logger

router = Router()

@router.message(Command("q_dr") or Command("dr_dialog"))
@d.bugreport
@filters.only_sentry_instance
@filters.only_groups
async def dr_dialog_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        if message.reply_to_message.text is None:
            await message.reply("⚠️ В данном сообщении отсутствует текст")
            return

        photos = await bot.get_user_profile_photos(message.reply_to_message.from_user.id, limit=1)

        if not photos.total_count:
            await message.reply(
                "⚠️ У пользователя отсутствует аватарка. \
Пользователи без аватарок пока не поддерживаются"
            )
            return

        msg = await message.reply("⏳ Видео в обработке, пожалуйста подождите...")

        file = await bot.get_file(photos.photos[0][-1].file_id)
        avatar_path = f"/tmp/avatar-{random.randint(1000, 9999999)}.jpeg"
        await bot.download_file(file.file_path, avatar_path)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "dr_dialog.py",
            avatar_path,
            message.reply_to_message.text[:500],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(stderr)
            await msg.edit_text(
                f"⚠️ Не удалось отрендерить диалоговое окно: \
процесс вернул код ошибки {process.returncode}"
            )
            return

        _, sep, video_path = stdout.decode().partition("--------PATH: ")
        if not sep:
            await msg.edit_text("⚠️ Не удалось отрендерить диалоговое окно: \
путь к видео не найден")
            return

        await msg.reply_video(types.FSInputFile(video_path))
        os.remove(video_path)
        os.remove(avatar_path)
    else:
        await message.reply("⚠️ Для создания диалогового окна вы должны ответить на сообщение")
