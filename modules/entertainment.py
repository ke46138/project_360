"""Модуль с развлекательными командами"""

import asyncio
import random
import re
import traceback
from html import escape
from io import BytesIO
import json

import aiohttp
from aiogram import Router, types, Bot
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.filters import Command
from aiogram.types import ReactionTypeEmoji
from openai import AsyncOpenAI
from openai import RateLimitError, APIError, InternalServerError

import config
# ! DEPRECATED: Нужно заменить на что-то более качественное или развивать этот форк
from dsk.api import DeepSeekAPI
from modules import async_tasks
from modules import auth
from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import redis
from modules import utils

api = DeepSeekAPI(config.DS_KEY)
client = AsyncOpenAI(
    base_url=config.AI_ENDPOINT,
    api_key=config.AI_API_KEY,
)
router: Router = Router()

weapons = (
    ["Пушистый шарф Ральзея", 999999999999999999, "шарфом"], # 0
    ["Палка", 10, "палкой"], # 1
    ["Грубые перчатки", 15, "грубыми перчатками"], # 2
    ["Секира Сьюзи", 60, "секирой"], # 3
    ["Шип", 30, "шипом"], # 4
    ["Меч 1x1x1x1", 25, "мечом 1x1x1x1"], # 5
    ["Пьяный габби", 9999999999999999, "кинул пьяного габби и он жёстко покусал"], # 6
    ["Пьяный посох дусекара", 700, "посохом"]  # 7
)
armors = (
    ["Плащ Ральзея", 99999999999],
    ["Бинт", 1],
    ["Мужицкая бандана", 2],
    ["Костюм горничной для мафиозо", 10]
)

DEEPSEEK_LOCK = False
DEEPSEEK_BANLIST = [0]
DS_ENABLED = True
HISTORY = []
last_used = {}

class DraftIDManager:
    def __init__(self, min_id=1, max_id=1000):
        self.min_id = min_id
        self.max_id = max_id
        self.used_ids = set()
        self.free_ids = set(range(min_id, max_id + 1))
        self.next_id = min_id

    def allocate(self):
        if not self.free_ids:
            raise Exception("Нет свободных ID")

        new_id = min(self.free_ids)
        self.free_ids.remove(new_id)
        self.used_ids.add(new_id)
        return new_id

    def release(self, draft_id):
        if draft_id in self.used_ids:
            self.used_ids.remove(draft_id)
            self.free_ids.add(draft_id)
        else:
            raise ValueError(f"ID {draft_id} не используется")

draft_manager = DraftIDManager()

async def load_history():
    """Загрузить историю нейросети"""
    temp = await sql.load_ai_history()
    for i in temp:
        HISTORY.append({"role": i[1], "content": i[2]})

def find_json_objects(text: str):
    decoder = json.JSONDecoder()
    results = []

    i = 0

    while i < len(text):
        char = text[i]

        if char in "{[":
            try:
                obj, end = decoder.raw_decode(text[i:])
                results.append(obj)

                i += end
                continue

            except json.JSONDecodeError:
                pass

        i += 1

    return results

async def ask_ai(usrmsg: str, message: types.Message, bot: Bot):
    try:
        HISTORY.append({"role": "user", "content": usrmsg})
        await sql.append_ai_history("user", usrmsg)
        completion = await client.chat.completions.create(
                model=config.AI_MODEL,
                messages=HISTORY
        )
        HISTORY.append({"role": "assistant", "content": completion.choices[0].message.content})
        if completion.choices[0].message.content:
            await sql.append_ai_history("assistant", completion.choices[0].message.content[0:2000])
            await message.edit_text(completion.choices[0].message.content[0:2000])
        else:
            await message.edit_text("⚠️ Нейросеть не ответила на сообщение")
    except RateLimitError as e:
        await message.edit_text(
            f"⚠️ Закончился лимит запросов. \
Повторите попытку завтра после 3:00 по МСК"
        )
    except InternalServerError as e:
        await message.edit_text(f"⚠️ Ошибка API. Повторите попытку позже. Ответ от openai: {e}")
    except APIError:
        await message.edit_text("⚠️ Ошибка API. Повторите попытку позже")
        await bot.send_message(
            config.DEV_ADMIN_USERID,
            f"⚠️ Ошибка API. \
Traceback: \
<pre>{escape(traceback.format_exc()[-1000:])}</pre>",
            parse_mode='HTML'
        )
    except:
        await d.send_view_traceback(message, traceback.format_exc(), bot, func="ask_ai")

@d.bugreport
async def ask_ai_deepseek(message: types.Message, bot: Bot, usrmsg: str):
    """Асинхронная задача для обработки запросов к дипсику"""
    global DEEPSEEK_LOCK

    DEEPSEEK_LOCK = True
    try:
        is_search = "--search" in usrmsg

        ai_msg = ""

        async for chunk in api.chat_completion_async(
            config.DS_CHATID,
            usrmsg,
            parent_message_id=await redis.get_deepseek_message_id(),
            search_enabled=is_search
        ):
            if chunk['type'] == 'message':
                ai_msg += chunk['content']
            if chunk['type'] == 'message_info':
                await redis.set_deepseek_message_id(chunk['message_id'])

        if ai_msg:
            await message.edit_text(escape(ai_msg[:2000]))
        else:
            await message.edit_text("⚠️ Нейросеть не ответила на сообщение")
    finally:
        DEEPSEEK_LOCK = False

@d.bugreport
async def ask_ai_deepseek_stream(message: types.Message, bot: Bot, usrmsg: str):
    """Асинхронная задача для обработки запросов к дипсику с поддержкой стриминга"""
    global DEEPSEEK_LOCK

    DEEPSEEK_LOCK = True

    try:
        is_search = "--search" in usrmsg

        ai_msg = ""
        draft_id = draft_manager.allocate()
        i = 0

        async for chunk in api.chat_completion_async(
            config.DS_CHATID,
            usrmsg,
            parent_message_id=await redis.get_deepseek_message_id(),
            search_enabled=is_search
        ):
            if chunk['type'] == 'message':
                ai_msg += chunk['content']
                if i % 30 == 0:
                    try:
                        await bot.send_message_draft(
                            chat_id=message.chat.id, 
                            draft_id=draft_id, 
                            text=escape(ai_msg[:2000])
                        )
                    except:
                        pass
            if chunk['type'] == 'message_info':
                await redis.set_deepseek_message_id(chunk['message_id'])
            i += 1

        if ai_msg != "":
            await message.reply(ai_msg[:2000])
        else:
            await message.reply("⚠️ Нейросеть не ответила на сообщение")

        draft_manager.release(draft_id)
    finally:
        DEEPSEEK_LOCK = False

@router.message(Command('ai'))
@d.bugreport
@filters.cooldown
@filters.only_sentry_instance
async def ai_command(message: types.Message, bot: Bot):
    """Создать запрос к ИИ"""
    user_message = message.text.split(' ', 1)[1] if ' ' in message.text else '' # type: ignore

    if user_message == '' or user_message == ' ':
        await message.reply("⚠️ Недостаточно аргументов. Использование: /ai Сообщение для ИИ")
        return

    if not HISTORY:
        await load_history()

    botmsg = await message.reply("Думаю...")

    await bot.send_chat_action(message.chat.id, action="typing")
    asyncio.create_task(
        ask_ai(
            f"{message.from_user.full_name} ({message.from_user.id}) сказал(а): {user_message}", # type: ignore
            botmsg,
            bot
        )
    )

@router.message(Command('ai_ds'))
@d.bugreport
@filters.cooldown
@filters.only_sentry_instance
async def ai_deepseek_command(message: types.Message, bot: Bot):
    """Создать запрос к дипсику"""
    if message.from_user.id in DEEPSEEK_BANLIST: # type: ignore
        await message.reply("⚠️ Вы были забанены разработчиком")
        return

    if not DS_ENABLED:
        await message.reply("⚠️ Команда отключена разработчиком")
        return

    if DEEPSEEK_LOCK:
        await message.reply("⚠️ Подождите выполнения другого запроса")
        return

    user_message = message.text.split(' ', 1)[1] if ' ' in message.text else '' # type: ignore
    if find_json_objects(user_message):
        await message.reply("⚠️ json документы запрещены")
        return
    user_message = user_message.replace("\"", '\\"')

    if user_message == '' or user_message == ' ':
        await message.reply(
            "⚠️ Недостаточно аргументов. Использование: /ai_ds Сообщение для ИИ"
        )
        return

    await bot.send_chat_action(message.chat.id, action="typing")

    if message.chat.type == "private":
        asyncio.create_task(
            ask_ai_deepseek_stream(
                message,
                bot,
                f"{{\"full_name\": \"{message.from_user.full_name}\", \"user_id\": {message.from_user.id}, \"user_message\": \"{user_message}\"}}" # type: ignore
            )
        )
    else:
        botmsg = await message.reply("Думаю...")
        asyncio.create_task(
            ask_ai_deepseek(
                botmsg,
                bot,
                f"{{\"full_name\": \"{message.from_user.full_name}\", \"user_id\": {message.from_user.id}, \"user_message\": \"{user_message}\"}}" # type: ignore
            )
        )

@router.message(Command('ds_toggle'))
@d.bugreport
@filters.only_sentry_instance
@auth.require_auth
async def ai_ds_enable_command(message: types.Message, bot: Bot):
    """Выключить/включить дипсик"""
    global DS_ENABLED

    if DS_ENABLED:
        DS_ENABLED = False
        await message.reply("🚫 Дипсик выключен")
    else:
        DS_ENABLED = True
        await message.reply("✅ Дипсик включён")

@router.message(Command('sync_ai_history'))
@d.bugreport
@filters.only_sentry_instance
@auth.require_auth
async def sync_ai_history_command(message: types.Message, bot: Bot):
    """Синхронизировать историю с бд"""
    global HISTORY

    HISTORY = []
    await load_history()
    await message.react([ReactionTypeEmoji(emoji='👍')])

@router.message(Command('attack'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.not_for_abrikos
async def attack_command(message: types.Message, bot: Bot):
    """Атаковать пользователя"""
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == utils.BOT_ID: # type: ignore
            await message.reply("⚠️ Нельзя использовать эту команду на боте")
            return

        if message.reply_to_message.from_user.id == message.from_user.id: # type: ignore
            await message.reply("⚠️ Нельзя атаковать самого себя")
            return

        player_ATK = await sql.get_dr_user(message.from_user.id, message.chat.id) # type: ignore
        player_DMG = await sql.get_dr_user(message.reply_to_message.from_user.id, message.chat.id) # type: ignore

        player_DMG_def = player_DMG[4] + player_DMG[6]
        player_ATK_atk = ((player_ATK[3] + player_ATK[6] + weapons[player_ATK[9]][1]) \
            * random.randint(1, 2)) - player_DMG_def
        player_ATK_exp = player_ATK[7]

        player_DMG_maxhp = 16 + (4 * player_DMG[6])
        if player_ATK_atk <= 0:
            player_ATK_atk = 1
        player_DMG_newhp = player_DMG[8] - player_ATK_atk

        assert message.from_user is not None
        await message.reply(
            f"{utils.wrap_user_link(message.from_user.full_name, message.from_user.id)} \
ударил(а) {weapons[player_ATK[9]][2]} \
{utils.wrap_user_link(
    message.reply_to_message.from_user.full_name, # type: ignore
    message.reply_to_message.from_user.id # type: ignore
)}. Нанесено {player_ATK_atk} урона"
        )

        if player_DMG_newhp <= 0:
            player_ATK_exp = player_ATK[7] + 50
            if player_ATK_exp >= player_ATK[6] * 100:
                await sql.update_dr_user(
                    message.from_user.id,
                    message.chat.id,
                    player_ATK[6] + 1,
                    player_ATK_exp,
                    player_ATK[8],
                    player_ATK[9],
                    player_ATK[10]
                )
                await sql.update_dr_user(
                    message.reply_to_message.from_user.id, # type: ignore
                    message.chat.id,
                    player_DMG[6],
                    player_DMG[7],
                    player_DMG_maxhp,
                    player_DMG[9],
                    player_DMG[10]
                )
                await message.reply("""
* Поздравляем!
* Вы выйграли! Вы получили 50 ОП.
* Ваш УР повысился.""")
            else:
                await sql.update_dr_user(
                    message.from_user.id,
                    message.chat.id,
                    player_ATK[6],
                    player_ATK_exp,
                    player_ATK[8],
                    player_ATK[9],
                    player_ATK[10]
                )
                await sql.update_dr_user(
                    message.reply_to_message.from_user.id, # type: ignore
                    message.chat.id,
                    player_DMG[6],
                    player_DMG[7],
                    player_DMG_maxhp,
                    player_DMG[9],
                    player_DMG[10]
                )
                await message.reply("""
* Поздравляем!
* Вы выйграли! Вы получили 50 ОП.""")
        else:
            await sql.update_dr_user(
                message.reply_to_message.from_user.id, # type: ignore
                message.chat.id,
                player_DMG[6],
                player_DMG[7],
                player_DMG_newhp,
                player_DMG[9],
                player_DMG[10]
            )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите атаковать")

@router.message(Command('dr_stats'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def dr_stats_command(message: types.Message, bot: Bot):
    player = await sql.get_dr_user(message.from_user.id, message.chat.id) # type: ignore
    await message.reply(f"""
Статистика:
УР: {player[6]}
ОЗ: {player[8]}/{16 + (player[6] * 4)}

АТК: {player[6]}({weapons[player[9]][1]}) ОП: {player[7]}
ЗЩТ {player[6]}({armors[player[10]][1]})

Оружие: {weapons[player[9]][0]}
Броня: {armors[player[10]][0]}""")

@router.message(Command('dr_heal'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def dr_heal_command(message: types.Message, bot: Bot):
    player = await sql.get_dr_user(message.from_user.id, message.chat.id) # type: ignore
    if player[8] + 5 > 16 + (player[6] * 4):
        await sql.update_dr_user(
            message.from_user.id, # type: ignore
            message.chat.id,
            player[6],
            player[7],
            16 + (player[6] * 4),
            player[9],
            player[10]
        )
        await message.reply("Ваши ОЗ восстановлены до максимума")
    else:
        await sql.update_dr_user(
            message.from_user.id, # type: ignore
            message.chat.id,
            player[6],
            player[7],
            player[8] + 5,
            player[9],
            player[10]
        )
        await message.reply("Вылечено 5 ОЗ")

@router.message(Command('beer_old'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def beer_old_command(message: types.Message, bot: Bot):
    await message.reply("🍺 Вы выпили пивко. ВАМ ХАРАШЕЧНА")

@router.message(Command('cigarette'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def cigarette_command(message: types.Message, bot: Bot):
    await message.reply("🚬 Вы закурили сигаретку. ВАМ ХАРАШЕЧНА")

@router.message(Command('roulette'))
@d.bugreport
@filters.only_groups
@filters.cooldown
async def russian_roulette_command(message: types.Message, bot: Bot):
    """Русская рулетка"""
    if random.random() <= 0.5:
        await message.reply("✅ Дробовик не выстрелил! Вы выиграли!")
    else:
        await message.reply(
            "🔫 Дробовик выстрелил! Произошёл шанс момент, вы проиграли 1000 тёмных рублей"
        )
        await sql.update_credit(message.from_user.id, message.chat.id, -1000) # type: ignore

@router.message(Command('yesno'))
@d.bugreport
@filters.only_groups
async def yesno_command(message: types.Message, bot: Bot):
    """Да/нет"""
    if random.random() <= 0.5:
        await message.reply("✅ Да")
    else:
        await message.reply("🚫 Нет")

@router.message(Command('random'))
@d.bugreport
@filters.only_groups
async def random_command(message: types.Message, bot: Bot):
    """Рандомайзер"""
    args = message.text.split() # type: ignore
    if len(args) < 3:
        await message.reply("⚠️ Недостаточно аргументов. Использование: /random <число1> <число2>")
        return

    await message.reply(f"🎲 Выпало число {random.randint(int(args[1]), int(args[2]))}")

@router.message(Command('dr_board'))
@d.bugreport
@filters.only_groups
async def dr_board_command(message: types.Message, bot: Bot):
    """Вывести таблицу лидеров по тёмным рублям"""
    result = await sql.get_social_credits(message.chat.id)

    if result == {}:
        await message.reply("⚠️ Ни у кого нет тёмных рублей. Таблица лидеров пуста")
        return

    msg = "📊 Топ 10 лидеров по тёмным рублям:\n\n"
    j = 1

    for i in result:
        try:
            user = await bot.get_chat_member(message.chat.id, i["userid"])
        except:
            await sql.delete_from_social_credit_table(i["userid"], message.chat.id)
            continue

        if user.status in ("restricted", "member", "administrator"):
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            msg += f"{j}. {utils.wrap_user_link(fullname, i["userid"])}, тёмных рублей: {i["credits"]} Т₽\n"
            j += 1
        else:
            await sql.delete_from_social_credit_table(user.user.id, message.chat.id)

    await message.reply(
        msg,
        parse_mode="HTML",
        disable_web_page_preview=True,
        disable_notification=True
    )

@router.message(Command('dr_board_debt'))
@d.bugreport
@filters.only_groups
async def dr_board_debt_command(message: types.Message, bot: Bot):
    """Вывести таблицу должников по тёмным рублям"""
    result = await sql.get_social_credits_debt(message.chat.id)

    if result == ():
        await message.reply("⚠️ Должники отсутствуют. Таблица лидеров пуста")
        return

    msg = "📊 Топ 10 должников по тёмным рублям:\n\n"
    j = 1

    for i in result:
        try:
            user = await bot.get_chat_member(message.chat.id, i["userid"])
        except:
            await sql.delete_from_social_credit_table(i["userid"], message.chat.id)
            continue

        if user.status in ("restricted", "member", "administrator"):
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            msg += f"{j}. {utils.wrap_user_link(fullname, i["userid"])}, тёмных рублей: {i["credits"]} Т₽\n"
            j += 1
        else:
            await sql.delete_from_social_credit_table(user.user.id, message.chat.id)

    await message.reply(
        msg,
        parse_mode="HTML",
        disable_web_page_preview=True,
        disable_notification=True
    )

@router.message(Command('give_money'))
@d.bugreport
async def give_credit_command(message: types.Message, bot: Bot):
    """Передать тёмные рубли пользователю"""
    if message.reply_to_message:
        args = message.text.split() # type: ignore
        if len(args) < 2:
            await message.reply(
                "⚠️ Недостаточно аргументов. \
Использование: /give_money положительное_число_рублей"
            )
            return

        try:
            money = int(args[1])
        except ValueError:
            await message.reply(
                "⚠️ Первый аргумент не число. \
Использование: /give_money положительное_число_рублей"
            )
            return

        if money < 0:
            await message.reply(
                "⚠️ Первый аргумент отрицательное число. \
Использование: /give_money положительное_число_рублей"
            )
            return

        result = await sql.get_user_social_credits(
            message.from_user.id, # type: ignore
            message.chat.id
        )

        if result["credits"] < money:
            await message.reply("⚠️ У вас недостаточно тёмных рублей")
            return

        await sql.update_credit(message.reply_to_message.from_user.id, message.chat.id, money) # type: ignore
        await sql.update_credit(message.from_user.id, message.chat.id, money * -1) # type: ignore

        await message.react([types.ReactionTypeEmoji(emoji='👍')])
    else:
        await message.reply(
            "⚠️ Вы должны ответить на сообщение пользователя, \
которому хотите передать тёмные рубли"
        )

@router.message(Command('update_credit'))
@d.bugreport
@auth.require_auth
async def add_credit_command(message: types.Message, bot: Bot):
    """Изменить тёмные рубли пользователя"""
    if message.reply_to_message:
        args = message.text.split() # type: ignore
        if len(args) < 2:
            await message.reply("⚠️ Недостаточно аргументов. \
Использование: /update_credit число_кредитов")

        try:
            int(args[1])
        except ValueError:
            await message.reply("⚠️ Первый аргумент не число. \
Использование: /update_credit число_кредитов")
            return

        await sql.update_credit(
            message.reply_to_message.from_user.id, # type: ignore
            message.chat.id,
            int(args[1])
        )

        await message.react([types.ReactionTypeEmoji(emoji='👍')])
    else:
        await message.reply(
            "⚠️ Вы должны ответить на сообщение пользователя, \
у которого хотите изменить тёмные рубли"
        )

@router.message(Command('wallet'))
@d.bugreport
@filters.only_groups
async def wallet_command(message: types.Message, bot: Bot):
    if message.reply_to_message and message.reply_to_message.from_user.id != 777000: # type: ignore
        result = await sql.get_user_social_credits(
            message.reply_to_message.from_user.id, # type: ignore
            message.chat.id
        )
        assert message.reply_to_message.from_user is not None
        fullname = f"{message.reply_to_message.from_user.first_name} \
{message.reply_to_message.from_user.last_name or ''}".strip()

        await message.reply(
            f"💵 Тёмных рублей в кошельке \
{utils.wrap_user_link(fullname, message.reply_to_message.from_user.id)}: \
{result["credits"]} Т₽",
            parse_mode="HTML"
        )

    else:
        result = await sql.get_user_social_credits(
            message.from_user.id, # type: ignore
            message.chat.id
        )

        await message.reply(f"💵 Тёмных рублей в кошельке: {result["credits"]} Т₽")

@router.message(Command('femboy'))
@d.bugreport
@filters.only_groups
async def femboy_command(message: types.Message, bot: Bot):
    await message.reply("✅ Вы теперь фембой")

@router.message(Command('dep'))
@d.bugreport
@filters.only_groups
@filters.cooldown
async def dep_command(message: types.Message, bot: Bot):
    """Если хочешь депнуть мне, то депай всё"""
    if random.random() <= 0.4:
        botmsg = await message.reply("💵 Вы выиграли 500 тёмных рублей!")
        await sql.update_credit(message.from_user.id, message.chat.id, 500) # type: ignore
    else:
        botmsg = await message.reply("🚫 Вы проиграли 100 тёмных рублей!")
        await sql.update_credit(message.from_user.id, message.chat.id, -100) # type: ignore

    asyncio.create_task(async_tasks.delete_msg(message, bot))
    asyncio.create_task(async_tasks.delete_msg(botmsg, bot))

@router.message(Command('donate_kirill'))
@d.bugreport
@filters.only_groups
@filters.cooldown
async def donate_kirill_command(message: types.Message, bot: Bot):
    await sql.update_credit(message.from_user.id, message.chat.id, -100) # type: ignore
    await sql.update_credit(1312172800, message.chat.id, 100)

    await message.reply("💵 Вы пожертвовали 100 тёмных рублей в культ Кирилла")

@router.message(Command('who'))
@d.bugreport
@filters.only_groups
async def who_command(message: types.Message, bot: Bot):
    user_message = message.text.split(' ', 1)[1] if ' ' in message.text else None # type: ignore

    if user_message == None:
        await message.reply("⚠️ Вы должны должны указать, что вы хотите узнать")
        return

    users = await sql.get_group_users(message.chat.id)
    try:
        userid = random.choice(users)
    except IndexError:
        await message.reply("⚠️ В списке нет пользователей. \
Чтобы добавить пользователей, \
скажите им перезайти в группу или написать любое сообщение")
        return
    user = await bot.get_chat_member(message.chat.id, userid)

    await message.reply(f"Я думаю, что {utils.wrap_user_link(user.user.full_name, user.user.id)} {user_message}")

@router.message(Command('chance'))
@d.bugreport
@filters.only_groups
async def chance_command(message: types.Message, bot: Bot):
    await message.reply(f"Я думаю, что вероятность {random.randint(0, 100)}%")

@router.message(Command('shipperim')) # type: ignore
@d.bugreport
@filters.only_groups
@filters.cooldown(ctime=30)
async def shipperim_command(message: types.Message, bot: Bot):
    users = await sql.get_group_users(message.chat.id)
    try:
        first_userid = random.choice(users)
        users.remove(first_userid)
        second_userid = random.choice(users)
    except IndexError:
        await message.reply("⚠️ В списке нет или недостаточно пользователей. \
Чтобы добавить пользователей, \
скажите им перезайти в группу или написать любое сообщение")
        return
    first_user = await bot.get_chat_member(message.chat.id, first_userid)
    second_user = await bot.get_chat_member(message.chat.id, second_userid)
    first_fullname = f"{first_user.user.first_name} {first_user.user.last_name or ''}".strip()
    second_fullname = f"{second_user.user.first_name} {second_user.user.last_name or ''}".strip()

    await message.reply(
        f"💞 Судя по гороскопу, \
{utils.wrap_user_link(first_fullname, first_userid)} + \
{utils.wrap_user_link(second_fullname, second_userid)} \
созданы друг для друга. Любите друг друга. Мяю 💋",
        parse_mode="HTML",
        disable_notification=True
    )

@router.message(Command('weather'))
@d.bugreport
@filters.cooldown
async def weather_command(message: types.Message, bot: Bot):
    city = message.text.split(' ', 1)[1] if ' ' in message.text else '' # type: ignore

    if city == "":
        await message.reply("⚠️ Укажите город, в котором хотите узнать погоду")
        return

    city = city.replace(" ", "+")

    weather = ""

    msg = await message.reply("⌛️ Получаю погоду...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{city}?lang=ru&0&T") as response:
                weather = await response.text()

                if weather == "" or weather == None or len(weather) < 10:
                    await msg.edit_text("⚠️ Ответ от API пустой. Повторите попытку позже")
                    return
    except:
        await message.reply("⚠️ Ошибка получения погоды")
        return

    weather = re.sub(r'\[\d+(;\d+)*m', '', weather)

    await msg.edit_text(f"<pre>{weather}</pre>", parse_mode="HTML")

@router.message(Command('cat')) # type: ignore
@d.bugreport
@filters.only_groups
@filters.cooldown(ctime=10)
async def cat_command(message: types.Message, bot: Bot):
    image_url = 0
    image = 0

    msg = await message.reply("⌛️ Получаю данные...")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.thecatapi.com/v1/images/search?api_key={config.CAT_API_KEY}"
        ) as response:
            if response.status != 200:
                await msg.edit_text(f"⚠️ API ответил с кодом ошибки {response.status}")
                return
            js = await response.json()
            image_url = js[0]["url"]
        async with session.get(image_url) as response:
            image = BytesIO(await response.read())

    image.seek(0)
    await message.reply_photo(types.BufferedInputFile(image.read(), filename="cat.jpg"))

@router.message(Command('cubes'))
@d.bugreport
@filters.only_groups
async def cubes_command(message: types.Message, bot: Bot):
    """Начать игру "Кубики" """
    if message.reply_to_message:
        if message.from_user.id == message.reply_to_message.from_user.id: # type: ignore
            await message.reply("⚠️ С самим собой в кубики играть нельзя")
            return
        if message.reply_to_message.from_user.id == utils.BOT_ID: # type: ignore
            await message.reply("⚠️ С ботом в кубики играть нельзя, он не умеет")
            return
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Сыграть",
                    callback_data=f"cubesyes:\
{message.from_user.id}:{message.reply_to_message.from_user.id}:{message.chat.id}", # type: ignore
                    style="success"
                ),
                types.InlineKeyboardButton(
                    text="Нет",
                    callback_data=f"cubesno:\
{message.from_user.id}:{message.reply_to_message.from_user.id}:{message.chat.id}", # type: ignore
                    style="danger"
                )
            ]
        ])

        await message.reply_to_message.reply(
            "🎲 Вас приглашают сыграть в кубики",
            reply_markup=markup
        )
    else:
        await message.reply(
            "⚠️ Вам нужно ответить на сообщение пользователя, с которым хотите сыграть в кубики"
        )

async def cubes_task(p1_id: int, p2_id: int, chat_id: int, bot: Bot, message: types.Message):
    """Асинхронная задача для игры Кубики"""
    try:
        first = await bot.send_dice(
            chat_id,
            emoji=DiceEmoji.DICE,
            reply_to_message_id=message.message_id
        )
        await asyncio.sleep(3.6)
        second = await bot.send_dice(
            chat_id,
            emoji=DiceEmoji.DICE,
            reply_to_message_id=message.message_id
        )
        await asyncio.sleep(3.6)

        first_user = await bot.get_chat_member(chat_id, p1_id)
        second_user = await bot.get_chat_member(chat_id, p2_id)

        if first.dice.value > second.dice.value: # type: ignore
            result_text = f"🎲 {utils.wrap_user_link(first_user.user.full_name, p1_id)} победил(а)"
        elif second.dice.value > first.dice.value: # type: ignore
            result_text = f"🎲 {utils.wrap_user_link(second_user.user.full_name, p2_id)} победил(а)"
        else:
            result_text = f"🎲 Ничья"

        await message.reply(result_text)
    except:
        await d.send_view_traceback(message, traceback.format_exc(), bot, func="cubes_task")

@router.message(Command('marriage'))
@d.bugreport
@filters.only_groups
async def marriage_command(message: types.Message, bot: Bot):
    """Предложить брак пользователю"""
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == message.from_user.id: # type: ignore
            await message.reply("⚠️ Вы не можете вступить в брак сами с собой")
            return

        first_user_marriages = await sql.get_marriages_user(
            message.chat.id,
            message.from_user.id # type: ignore
        )
        second_user_marriages = await sql.get_marriages_user(
            message.chat.id,
            message.reply_to_message.from_user.id # type: ignore
        )

        if first_user_marriages:
            await message.reply(
                "⚠️ Вы уже состоите в браке. Чтобы развестись, введите команду /divorce"
            )
            return
        elif second_user_marriages:
            await message.reply(
                "⚠️ Пользователь, с которым вы хотите вступить в брак уже в браке"
            )
            return

        fullname = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip() # type: ignore

        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Согласиться", # структура marrage:чатид:первыйид:второйид
                    callback_data=f"marriage:\
{message.chat.id}:{message.from_user.id}:{message.reply_to_message.from_user.id}", # type: ignore
                    style="success"
                )
            ]
        ])

        await message.reply_to_message.reply(
            f"💖 Вам предлагают вступить в брак с \
{utils.wrap_user_link(fullname, message.from_user.id)}", # type: ignore
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=markup
        )
    else:
        await message.reply(
            "⚠️ Вам нужно ответить на сообщение пользователя, с которым хотите вступить в брак"
        )

@router.message(Command("marriages"))
@d.bugreport
@filters.only_groups
async def marriages_command(message: types.Message, bot: Bot):
    """Посмотреть все браки в чате"""
    marriages = await sql.get_marriages_chat(message.chat.id)
    msg = "⚠️ Этого не должно быть"

    if marriages == ():
        msg = "⚠️ В данной группе нет браков"
    else:
        msg = "💍 Браки этой группы\n\n"
        n = 1
        for i in marriages:
            first_user = await bot.get_chat_member(i[1], i[2])
            second_user = await bot.get_chat_member(i[1], i[3])
            time_passed = utils.humanize_timestamp(i[4])
            msg += f"{n}. {utils.wrap_user_link(first_user.user.full_name, i[2])} + \
{utils.wrap_user_link(second_user.user.full_name, i[3])}, {time_passed}\n"
            n += 1

    await message.reply(
        msg,
        parse_mode='HTML',
        disable_web_page_preview=True,
        disable_notification=True
    )

@router.message(Command('divorce'))
@d.bugreport
@filters.only_groups
async def divorce_command(message: types.Message, bot: Bot):
    """Развестись"""
    user_marriages = await sql.get_marriages_user(message.chat.id, message.from_user.id) # type: ignore

    if not user_marriages:
        await message.reply("⚠️ Вы не состоите в браке")
        return

    fullname = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip() # type: ignore
    second_user = await bot.get_chat_member(message.chat.id, user_marriages["second_id"])
    second_fullname = f"{second_user.user.first_name} {second_user.user.last_name or ''}".strip()

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Да",
                    callback_data=f"divorceyes:{user_marriages["first_id"]}:{user_marriages["second_id"]}",
                    style="danger"
                ),
                types.InlineKeyboardButton(
                    text="Нет",
                    callback_data=f"divorceno",
                    style="success"
                )
            ]
        ]
    )

    if user_marriages["first_id"] == message.from_user.id: # type: ignore
        await message.reply(
            f"⚠️ Вы уверены, что хотите развестись с \
{utils.wrap_user_link(second_fullname, user_marriages["second_id"])}?",
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=markup
        )
    else:
        await message.reply(
            f"⚠️ Вы уверены, что хотите развестись с \
{utils.wrap_user_link(fullname, user_marriages["first_id"])}?",
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=markup
        )

async def callback_query(call: types.CallbackQuery, bot: Bot):
    try:
        if call.data.startswith("cubesyes"): # type: ignore
            _, p1_id, p2_id, chat_id = call.data.split(":") # type: ignore
            p1_id, p2_id, chat_id = int(p1_id), int(p2_id), int(chat_id)

            if call.from_user.id not in (p1_id, p2_id):
                await call.answer("⚠️ Это не тебе", show_alert=True)
                return

            if call.from_user.id != p2_id:
                await call.answer("⚠️ Ты не можешь принять за другого", show_alert=True)
                return

            await call.message.edit_text("🎲 Бросаю кубики...") # type: ignore

            asyncio.create_task(cubes_task(p1_id, p2_id, chat_id, bot, call.message)) # type: ignore
        elif call.data.startswith("cubesno"): # type: ignore
            _, p1_id, p2_id, chat_id = call.data.split(":") # type: ignore
            p1_id, p2_id, chat_id = int(p1_id), int(p2_id), int(chat_id)

            if call.from_user.id not in (p1_id, p2_id):
                await call.answer("⚠️ Это не тебе", show_alert=True)
                return

            if call.from_user.id != p2_id:
                await call.answer("⚠️ Ты не можешь отклонить за другого", show_alert=True)
                return

            await call.message.delete() # type: ignore
            await call.answer("Нет значит нет")
        elif call.data.startswith("marriage"): # type: ignore
            _, chatid, first_userid, second_userid = call.data.split(":") # type: ignore

            if call.message.chat.id != int(chatid): # type: ignore
                await call.answer("⚠️ Ошибка: не тот чат", show_alert=True)
                return

            if call.from_user.id != int(second_userid):
                await call.answer("⚠️ Вы не можете принять брак за другого", show_alert=True)
                return

            user_marriages = await sql.get_marriages_user(call.message.chat.id, call.from_user.id) # type: ignore

            if user_marriages:
                await call.answer("⚠️ Вы уже состоите в браке", show_alert=True)
                return

            await sql.add_marriage(chatid, int(first_userid), int(second_userid))

            await call.message.edit_text("💍 Вы успешно вступили в брак!") # type: ignore
            await call.answer("Готово!")
        elif call.data.startswith("divorceyes"): # type: ignore
            _, first_user, second_user = call.data.split(":") # type: ignore

            if call.from_user.id != call.message.reply_to_message.from_user.id: # type: ignore
                await call.answer("⚠️ Это не тебе", show_alert=True)
                return

            first_user = int(first_user)
            second_user = int(second_user)
            first_user_profile = await bot.get_chat_member(call.message.chat.id, first_user) # type: ignore
            second_user_profile = await bot.get_chat_member(call.message.chat.id, second_user) # type: ignore
            fullname = f"{first_user_profile.user.first_name} {first_user_profile.user.last_name or ''}".strip()
            second_fullname = f"{second_user_profile.user.first_name} {second_user_profile.user.last_name or ''}".strip()

            await sql.remove_marriage(call.message.chat.id, first_user, second_user) # type: ignore

            if call.message.reply_to_message.from_user.id == first_user: # type: ignore
                await call.message.edit_text( # type: ignore
                    f"💔 {utils.wrap_user_link(second_fullname, second_user)}, \
{utils.wrap_user_link(fullname, first_user)} \
подал(а) на развод. Вы больше не состоите в браке",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            else:
                await call.message.edit_text( # type: ignore
                    f"💔 {utils.wrap_user_link(fullname, first_user)}, \
{utils.wrap_user_link(second_fullname, second_user)} \
подал(а) на развод. Вы больше не состоите в браке",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

            await call.answer("Готово!")
        elif call.data.startswith("divorceno"): # type: ignore
            if call.from_user.id != call.message.reply_to_message.from_user.id: # type: ignore
                await call.answer("⚠️ Это не тебе", show_alert=True)
                return

            await call.message.delete() # type: ignore
            await call.answer("Готово!")
    except:
        await d.send_view_traceback(
            call.message, # type: ignore
            traceback.format_exc(),
            bot,
            func="callback_query"
        )
