"""Модуль для вызова генератора диалогов в стиле Deltarune"""

import asyncio
import os
import random
import sys
from pathlib import Path

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import filters
from modules import botdebug as d
from modules.logger import logger

router = Router()
RENDERER_SCRIPT = str(Path(__file__).parent / "dr_dialog_renderer.py")

@router.message(Command("q_dr", "dr_dialog"))
@d.bugreport
@filters.only_sentry_instance
@filters.only_groups
async def dr_dialog_command(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("⚠️ Для создания диалогового окна вы должны ответить на сообщение")
        return

    if not message.reply_to_message.text:
        await message.reply("⚠️ В данном сообщении отсутствует текст")
        return

    photos = await bot.get_user_profile_photos(message.reply_to_message.from_user.id, limit=1)
    if not photos.total_count:
        await message.reply(
            "⚠️ У пользователя отсутствует аватарка. Пользователи без аватарок пока не поддерживаются"
        )
        return

    msg = await message.reply("⏳ Видео в обработке, пожалуйста подождите...")

    avatar_path = f"/tmp/avatar-{random.randint(1000, 9999999)}.jpeg"
    video_path = None
    try:
        file = await bot.get_file(photos.photos[0][-1].file_id)
        await bot.download_file(file.file_path, avatar_path)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            RENDERER_SCRIPT,
            avatar_path,
            message.reply_to_message.text[:500],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error("Ошибка рендера dr_dialog: %s", stderr.decode(errors="replace"))
            await msg.edit_text(
                f"⚠️ Не удалось отрендерить диалоговое окно: процесс вернул код ошибки {process.returncode}"
            )
            return

        _, sep, video_path = stdout.decode(errors="replace").partition("--------PATH: ")
        if not sep or not video_path:
            await msg.edit_text("⚠️ Не удалось отрендерить диалоговое окно: путь к видео не найден")
            return

        video_path = video_path.strip()
        if os.path.exists(video_path):
            await msg.reply_video(types.FSInputFile(video_path))
        else:
            await msg.edit_text("⚠️ Не удалось найти сгенерированное видео на диске")
    except Exception as e:
        logger.exception("Ошибка при обработке dr_dialog: %s", e)
        await msg.edit_text(f"⚠️ Произошла ошибка: {e}")
    finally:
        if os.path.exists(avatar_path):
            try:
                os.remove(avatar_path)
            except OSError:
                pass
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except OSError:
                pass
