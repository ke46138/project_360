import random
import re
import time
from html import escape

from aiogram import Router, types, Bot
from aiogram.filters import BaseFilter

from modules import auth
from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import utils
from modules.logger import logger

MUTE_MODER_EMOJIS = [
    "👺",
    "🦸",
    "👮‍"
]

TIME_UNITS = (
    r'(минута|минуты|минут|минуту|'
    r'час|часа|часов|'
    r'день|дня|дней|'
    r'неделя|недели|недель|неделю|'
    r'месяц|месяца|месяцев|'
    r'год|года|лет)'
)

MODER_PATTERN = re.compile(
    r"""
    ^(\+модер|повысить)
    (?:\s+(?P<number>\d+))?
    (?:\s+(?P<target>@\w+|\d+))?
    \s*$
    """,
    re.VERBOSE
)
DEL_MODER_PATTERN = re.compile(
    r"""
    ^(снять|разжаловать)
    (?:\s+(?P<target>@\w+|\d+))?
    \s*$
    """,
    re.VERBOSE
)
MUTE_PATTERN = re.compile(
    rf"""
    ^(?P<command>заткнуть|мут|mute)
    \s*
    (?:
        (?P<time>\d+)\s+
        (?P<unit>минут[а-я]*|час[а-я]*|день[а-я]*|недел[а-я]*|месяц[а-я]*|год[а-я]*)
        \s*
    )?
    (?:
        @(?P<target>[a-zA-Z0-9_]+)
    )?
    \s*
    (?: \n (?P<reason>.+?) )?
    \s*$
    """,
    re.VERBOSE
)

router = Router()

class TextCommand(BaseFilter):
    def __init__(self, commands: list, method="default") -> None:
        self.commands = commands
        self.method = method

    async def __call__(self, message: types.Message) -> bool | dict:
        if not message.text:
            return
        for command in self.commands:
            if self.method == "default":
                self.command_words = command.lower().split()
                self.command_length = len(self.command_words)

                if not message.text:
                    return False

                text = message.text.lower()
                words = text.strip().split()

                if len(words) < self.command_length:
                    continue

                incoming_command = words[:self.command_length]

                if incoming_command != self.command_words:
                    continue

                return {"text": text}
            elif self.method == "full_comparsion":
                if command.lower() == message.text.lower():
                    return {"text": message.text.lower()}

        return False

def convert_time_unit_to_seconds(time_unit):
    if time_unit in ("минута", "минуты", "минут", "минуту"):
        return 60
    elif time_unit in ("час", "часа", "часов"):
        return 3600
    elif time_unit in ("день", "дня", "дней"):
        return 86400
    elif time_unit in ("неделя", "недели", "недель", "неделю"):
        return 604800
    elif time_unit in ("месяц", "месяца", "месяцев"):
        return 2592000
    elif time_unit in ("год", "года", "лет"):
        return 31536000
    else:
        return 0

@router.message(TextCommand(["мут", "заткнуть", "mute"]))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=100)
async def mute_command(message: types.Message, bot: Bot, text: str):
    match = MUTE_PATTERN.match(text)

    if not match:
        return

    target_raw = match.group("target")
    time_value = match.group("time")
    time_unit = match.group("unit")
    reason = match.group("reason")

    if target_raw is None:
        target = None
    elif target_raw.startswith("@"):
        target = target_raw
    else:
        try:
            target = int(target_raw)
        except ValueError:
            target = None

    if not target and message.reply_to_message:
        target = message.reply_to_message.from_user.id

    if not target:
        return

    try:
        user = await bot.get_chat_member(message.chat.id, target)
    except:
        await message.reply("📝 Не могу найти информацию о пользователе")
        return

    if time_value and time_unit:
        mute_until = time.time() + int(time_value) * convert_time_unit_to_seconds(time_unit)
        if mute_until == 0:
            logger.info("time = 0")
            return
        mute_relative = int(time.time()) - int(time_value) * convert_time_unit_to_seconds(time_unit)
    else:
        result = await sql.get_group_default_mute(message.chat.id)
        mute_until = time.time() + result
        mute_relative = int(time.time()) - result

    time_string = utils.humanize_timestamp(mute_relative)

    if reason:
        final_reason = f"💬 Причина: {escape(reason)}"
    else:
        final_reason = ""

    try:
        await bot.restrict_chat_member(
            message.chat.id,
            user.user.id,
            types.ChatPermissions(can_send_messages=False),
            until_date=mute_until
        )
    except Exception as e:
        await message.reply(
            f"""
⚠️ Ошибка Телеграм:

{e}
"""
        )
        return

    await message.reply(
        f"""
🔇 {utils.wrap_user_link(user.user.full_name, user.user.id)} лишается права слова на {time_string}
{final_reason}
{random.choice(MUTE_MODER_EMOJIS)} Модератор: {utils.wrap_actor_link(message)}
"""
    )

@router.message(TextCommand(["кто админ", "а судьи кто", "!staff", "!управляющие", "!админы", "ирис админы", "360 админы", ".админы"]))
@filters.only_groups
@d.bugreport
async def admins_command(message: types.Message, bot: Bot, text: str):
    bot_admins = await sql.get_group_admins(message.chat.id, bot)
    tg_admins = await bot.get_chat_administrators(message.chat.id)

    strings = []

    devs = [uid for uid, lvl in bot_admins if lvl == 255]
    admins = [uid for uid, lvl in bot_admins if lvl == 200]
    moders = [uid for uid, lvl in bot_admins if 100 <= lvl < 200]

    if devs:
        strings.append("🏆 Разработчик")
        for n in devs:
            user = await bot.get_chat_member(message.chat.id, n)
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            strings.append(utils.wrap_user_link(fullname, n))
    if admins:
        strings.append("⭐️⭐️⭐️⭐️⭐️ Создатель")
        for n in admins:
            user = await bot.get_chat_member(message.chat.id, n)
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            strings.append(utils.wrap_user_link(fullname, n))
    if moders:
        strings.append("⭐️⭐️ Старший модератор")
        for n in moders:
            user = await bot.get_chat_member(message.chat.id, n)
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            strings.append(utils.wrap_user_link(fullname, n))

    if strings == [] or strings is None:
        strings = ["🗓 В этом чате царит анархия"]

    await message.reply("\n".join(strings), parse_mode='HTML', disable_notification=True)

@router.message(TextCommand(["пинг"], method="full_comparsion"))
@d.bugreport
async def ping_command(message: types.Message, bot: Bot, text: str):
    await message.reply("ПОНГ")

@router.message(TextCommand(["бот"], method="full_comparsion"))
@d.bugreport
async def bot_command(message: types.Message, bot: Bot, text: str):
    await message.reply("✅ На месте")

@router.message(TextCommand(["снять", "разжаловать"]))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def del_admin_command(message: types.Message, bot: Bot, text: str):
    match = DEL_MODER_PATTERN.match(text)

    if not match:
        return

    target_raw = match.group("target")

    if target_raw is None:
        target = None
    elif target_raw.startswith("@"):
        target = target_raw
    else:
        try:
            target = int(target_raw)
        except ValueError:
            target = None

    if not target and message.reply_to_message:
        target = message.reply_to_message.from_user.id

    if not target:
        await message.reply("📝 Пользователь не был модератором")
        return

    try:
        user = await bot.get_chat_member(message.chat.id, target)
        user_id = user.user.id
    except:
        await message.reply("📝 Нет информации о пользователе")
        return

    admins = await sql.get_group_admins(message.chat.id, bot)

    for admin in admins:
        if user_id == admin[0]:
            admins.remove(admin)
            await sql.set_group_admins(message.chat.id, admins)
            await message.reply(f"❎ Модератор {utils.wrap_user_link(user.user.full_name, user_id)} разжалован(а)")
            return

    await message.reply("📝 Пользователь не был модератором")

@router.message(TextCommand(["+модер", "повысить"]))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def pmoder_command(message: types.Message, bot: Bot, text: str):
    match = MODER_PATTERN.match(text)

    if not match:
        return

    try:
        new_level = int(match.group("number") or 100)
    except ValueError:
        return
    target_raw = match.group("target")

    if target_raw is None:
        target = None
    elif target_raw.startswith("@"):
        target = target_raw
    else:
        try:
            target = int(target_raw)
        except ValueError:
            target = None

    if not target and message.reply_to_message:
        target = message.reply_to_message.from_user.id

    if not target:
        await message.reply("📝 Пользователь не указан")
        return

    try:
        user = await bot.get_chat_member(message.chat.id, target)
        user_id = user.user.id
    except:
        await message.reply("📝 Нет информации о пользователе")
        return

    if 100 <= new_level < 200:
        new_level_name = "модератором"
    elif new_level == 200:
        new_level_name = "главным админом"
    else:
        new_level_name = "никем"

    admins = await sql.get_group_admins(message.chat.id, bot)
    index = 0
    is_user_admin = False
    for i in admins:
        if user_id == i[0]:
            is_user_admin = True
            break
        index += 1

    if is_user_admin:
        if new_level > admins[index][1]:
            admins[index][1] = new_level
            await message.reply(f"✅ {utils.wrap_user_link(user.user.full_name, user_id)} назначен(а) {new_level_name} [{new_level}]")
        else:
            await message.reply("📝  уже на этой должности или выше")
            return
    else:
        if new_level < 100:
            new_level = 100
            new_level_name = "модератором"

        admins.append([user_id, new_level])

        await message.reply(f"✅ {utils.wrap_user_link(user.user.full_name, user_id)} назначен(а) {new_level_name} [{new_level}]")

    await sql.set_group_admins(message.chat.id, admins)
