import re

from aiogram import Router, types, Bot
from aiogram.filters import Command

from modules import auth
from modules import botdebug as d
from modules import filters

EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "]+",
    re.UNICODE
)

router = Router()

@router.message(Command("set_tag"))
@d.bugreport
@filters.only_groups
@filters.no_groups
@auth.require_auth(level=100)
async def set_tag_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        args = message.text.split()

        if len(args) < 2:
            await message.reply("⚠️ Недостаточно аргументов. Укажите тег после команды")
            return

        tag = EMOJI_RE.sub("", " ".join(args[1:])[:16])

        try:
            await bot.set_chat_member_tag(message.chat.id, message.reply_to_message.from_user.id, tag)
        except:
            await message.reply("⚠️ Не удалось изменить тег. Возможно, у бота нет прав на это")
            return

        await message.react([types.ReactionTypeEmoji(emoji='👍')])
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, у которого хотите изменить тег")
