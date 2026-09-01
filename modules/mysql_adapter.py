"""Адаптер для работы с базой данных mysql

А не спеть ли мне песню? АААААААААААА"""

import ast
import time
import asyncio

import aiomysql
from aiogram import Bot
from cachetools import TTLCache
from cachetools_async import cached

from modules.logger import logger

import config

THEME_CACHE = TTLCache(100, 30)
ANTIFLOOD_CACHE = TTLCache(100, 30)

pool: aiomysql.Pool = None

async def init():
    """Создаёт подключение и инициализирует базу данных с таблицами"""
    global pool

    logger.info("Инициализация базы данных MySQL")

    pool = await aiomysql.create_pool(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        db=config.MYSQL_DATABASE,
        autocommit=True,
        pool_recycle=3600
    )

    logger.info("База данных инициализирована")

async def close():
    logger.info("Закрытие пула базы данных")
    pool.close()
    await pool.wait_closed()

async def add_user(userid, chatid):
    """Добавляет пользователя в таблицу с пользователями"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT IGNORE INTO users_table (id, chatid) VALUES (%s, %s)',
                (userid, chatid,)
            )

async def remove_user(userid, chatid):
    """Убирает пользователя из таблицы с пользователями"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'DELETE FROM users_table WHERE id = %s AND chatid = %s',
                (userid, chatid,)
            )

async def add_user_many(queries):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.executemany(
                "INSERT IGNORE INTO users_table (id, chatid) VALUES (%s, %s)",
                queries
            )

async def write_statistics(command, exec_time, userid, chatid):
    """Записывает время выполнения хандлера в базу данных"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
INSERT INTO command_execution_time (time, userid, chatid, command, exec_time)
VALUES (%s, %s, %s, %s, %s)""",
(time.time(), userid, chatid, command, exec_time,)
            )

async def get_performance():
    """Получить статистику о производительности бота"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
SELECT * FROM `command_execution_time` WHERE `command`
LIKE \'%/%\' ORDER BY `time` DESC LIMIT 80"""
            )
            return list(await cursor.fetchall())[::-1]

async def get_msg_flow():
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
SELECT COUNT(*) FROM `command_execution_time`
WHERE time >= UNIX_TIMESTAMP() - 1"""
            )
            per_second = (await cursor.fetchone())[0]

            await cursor.execute(
                """
SELECT COUNT(*) FROM `command_execution_time`
WHERE time >= UNIX_TIMESTAMP() - 60"""
            )
            per_minute = (await cursor.fetchone())[0]

            await cursor.execute(
                """
SELECT COUNT(*) FROM `command_execution_time`
WHERE time >= UNIX_TIMESTAMP() - 3600"""
            )
            per_hour = (await cursor.fetchone())[0]

            await cursor.execute(
                """
SELECT COUNT(*) FROM `command_execution_time`
WHERE time >= UNIX_TIMESTAMP() - 86400"""
            )
            per_day = (await cursor.fetchone())[0]

            return per_second, per_minute, per_hour, per_day

async def truncate_perf():
    """Убирает все старые записи (>24 часов) из таблицы command_execution_time"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
DELETE FROM command_execution_time
WHERE time < (UNIX_TIMESTAMP() - 86400)"""
            )

async def load_ai_history():
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM `ai_history` ORDER BY n ASC;')
            return await cursor.fetchall()

async def append_ai_history(role, message):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO `ai_history` (role, message) VALUES (%s, %s);',
                (role, message,)
            )

async def get_social_credits(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT * FROM social_credit WHERE chatid = %s ORDER BY credits DESC LIMIT 10;',
                (chatid,)
            )
            return await cursor.fetchall()

async def get_social_credits_debt(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
SELECT * FROM social_credit
WHERE chatid = %s AND credits < 0 ORDER BY credits ASC LIMIT 10""",
                (chatid,)
            )
            return await cursor.fetchall()

async def get_user_social_credits(userid: int, chatid: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT * FROM social_credit WHERE userid = %s AND chatid = %s',
                (userid, chatid,)
            )
            result = await cursor.fetchall()
            if not result:
                await cursor.execute(
                    'INSERT INTO social_credit (userid, chatid, credits) VALUES (%s, %s, %s)',
                    (userid, chatid, 0,)
                )
            await cursor.execute(
                'SELECT * FROM social_credit WHERE userid = %s AND chatid = %s',
                (userid, chatid,)
            )
            return await cursor.fetchone()

async def update_credit(userid: int, chatid: int | str, money: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT * FROM social_credit WHERE userid = %s AND chatid = %s',
                (userid, chatid,)
            )
            result = await cursor.fetchall()
            if result is None or result == ():
                await cursor.execute(
                    'INSERT INTO social_credit (userid, chatid, credits) VALUES (%s, %s, %s)',
                    (userid, chatid, money,)
                    )
                return
            await cursor.execute(
                'UPDATE social_credit SET credits = credits + %s WHERE userid = %s AND chatid = %s;',
                (money, userid, chatid,)
                )

async def delete_from_social_credit_table(userid: int, chatid: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'DELETE FROM social_credit WHERE userid = %s AND chatid = %s',
                (userid, chatid,)
            )

async def get_dr_user(userid, chatid):
    """Получить пользователя и его характеристики"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT * FROM users_dr_settings WHERE id = %s AND chatid = %s',
                (userid, chatid,)
            )
            result = await cursor.fetchone()
            if result == [] or result == () or result is None:
                await cursor.execute(
                    '''
INSERT INTO users_dr_settings
(id, chatid, bonusATK, bonusDEF, baseHP, love, exp, HP, weaponId, armorId)
VALUES (%s, %s, 0, 0, 20, 1, 0, 20, 1, 1)''',
                    (userid, chatid,)
                )
                await cursor.execute(
                    'SELECT * FROM users_dr_settings WHERE id = %s AND chatid = %s',
                    (userid, chatid,)
                )
                result = await cursor.fetchone()
            return result

async def update_dr_user(userid, chatid, love, exp, hp, weaponId, armorId):
    """Обновить игрока"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                '''UPDATE users_dr_settings
SET love = %s, exp = %s, HP = %s, weaponId = %s, armorId = %s
WHERE id = %s AND chatid = %s;''',
                (love, exp, hp, weaponId, armorId, userid, chatid,)
            )

async def create_group(cursor, chatid):
    await cursor.execute(
        """
INSERT IGNORE INTO group_settings
(chatid) VALUES (%s)""",
        (chatid,)
    )

async def update_group_rules(chatid, rules):
    """Обновить правила группы"""
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT id FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)
            await cursor.execute(
                "UPDATE group_settings SET rules = %s WHERE chatid = %s",
                (rules, chatid,)
            )

async def get_group_rules(chatid):
    """Получить правила группы"""
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT rules FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)
                return "Не задано"
            return result["rules"]

async def update_group_hello(chatid, hello):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT id FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)
            await cursor.execute(
                "UPDATE group_settings SET hello_message = %s WHERE chatid = %s",
                (hello, chatid,)
            )

async def toggle_group_hello(chatid: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT hello_message_enabled FROM group_settings WHERE chatid = %s",
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)

            await cursor.execute(
                """
UPDATE group_settings SET hello_message_enabled = NOT hello_message_enabled WHERE chatid = %s;""",
                (chatid,)
            )
            await cursor.execute(
                """
SELECT hello_message_enabled FROM group_settings WHERE chatid = %s;""",
                (chatid,)
            )

            return (await cursor.fetchone())["hello_message_enabled"]

async def get_group_hello(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
SELECT hello_message_enabled, hello_message
FROM group_settings WHERE chatid = %s""",
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)
                return "Не задано"
            if result["hello_message_enabled"]:
                return result["hello_message"]
            return False

async def get_urlfilter_enabled(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT urlfilter_enabled FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)
                return False
            return result["urlfilter_enabled"]

async def get_group_default_mute(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT default_mute_time FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)
                return 900
            return result["default_mute_time"]

@cached(ANTIFLOOD_CACHE)
async def get_antiflood_enabled(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT antiflood_enabled FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            logger.info(result)
            if result is None:
                await create_group(cursor, chatid)
                return False
            return result.get("antiflood_enabled", False)

async def find_creator(chatid, bot: Bot):
    admins = await bot.get_chat_administrators(chatid)

    creator = 0

    for i in admins:
        if i.status == "creator":
            if i.user.first_name != "":
                creator = i.user.id
                break

    return creator

async def get_group_admins(chatid, bot: Bot):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT admins FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None or result == []:
                await create_group(cursor, chatid)

                creator = await find_creator(chatid, bot)

                if creator != 0:
                    await cursor.execute(
                        "UPDATE group_settings SET admins = %s WHERE chatid = %s",
                        (f"[[{creator}, 200]]", chatid,)
                    )
                    return [[creator, 200]]
                else:
                    return []
            elif result["admins"] == "" or result["admins"] == "[]":
                creator = await find_creator(chatid, bot)

                if creator != 0:
                    await cursor.execute(
                        "UPDATE group_settings SET admins = %s WHERE chatid = %s",
                        (f"[[{creator}, 200]]", chatid,)
                    )
                    return [[creator, 200]]
                else:
                    return []

            return ast.literal_eval(result["admins"])

async def set_group_admins(chatid, admins):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "UPDATE group_settings SET admins = %s WHERE chatid = %s",
                (str(admins), chatid,)
            )

async def update_urlfilter_enabled(chatid, isEnabled):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                'SELECT id FROM group_settings WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchone()
            if result == None or result == []:
                await create_group(cursor, chatid)
            await cursor.execute(
                "UPDATE group_settings SET urlfilter_enabled = %s WHERE chatid = %s",
                (isEnabled, chatid,)
            )

async def get_group_users(chatid):
    """Получить пользователей группы"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT * FROM users_table WHERE chatid = %s',
                (chatid,)
            )
            result = await cursor.fetchall()
            users = []
            for i in result:
                users.append(i[0])
            return users

async def get_all_group_users():
    """Получить всех пользователей"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM users_table')
            return await cursor.fetchall()

async def load_users_db():
    """Загрузить пользователей из бд"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT id, chatid FROM `users_table`')
            return await cursor.fetchall()

async def get_marriages_user(chatid, userid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
SELECT * FROM `marriages`
WHERE chatid = %s AND (first_id = %s or second_id = %s)""",
                (chatid, userid, userid,)
            )
            return await cursor.fetchone()

async def get_marriages_chat(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT * FROM `marriages` WHERE chatid = %s',
                (chatid,)
            )
            return await cursor.fetchall()

async def add_marriage(chatid, first_userid, second_userid):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
INSERT INTO `marriages` (chatid, first_id, second_id, time)
VALUES (%s, %s, %s, %s)""",
                (chatid, first_userid, second_userid, time.time(),)
            )

async def remove_marriage(chatid, first_userid, second_userid):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
DELETE FROM `marriages`
WHERE chatid = %s
AND ((first_id = %s AND second_id = %s)
OR (second_id = %s AND first_id = %s))""",
                (chatid, first_userid, second_userid, first_userid, second_userid,)
            )

async def add_whisper(user, text):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO `whisper` (time, user, content) VALUES (%s, %s, %s)',
                (time.time(), user, text,)
            )
            return cursor.lastrowid

async def get_whisper(whisper_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT * FROM `whisper` WHERE n = %s', (whisper_id,)
            )
            return await cursor.fetchone()

async def add_suggestion(userid: int, username: str, text: str):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
INSERT INTO `suggestions` \
(userid, username, text, created_at) \
VALUES (%s, %s, %s, %s)""",
                (userid, username, text, time.time())
            )

async def get_all_suggestions():
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM `suggestions`")
            return await cursor.fetchall()

async def create_beer_user(cursor, chatid, userid, last_drink=0, drinked=0):
    await cursor.execute(
        """
INSERT INTO `beer`
(chatid, userid, last_drink, drinkedtotal, progress)
VALUES (%s, %s, %s, %s, 0)""",
        (chatid, userid, last_drink, drinked,)
    )

    return cursor.lastrowid

async def get_user_beer(chatid: int, userid: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM `beer` WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )
            result = await cursor.fetchone()

            if result is None or result == ():
                row = await create_beer_user(cursor, chatid, userid)
                return {
                    "n": row,
                    "userid": userid,
                    "chatid": chatid,
                    "last_drink": 0,
                    "drinkedtotal": 0,
                    "progress": 0
                }

            return result

async def add_drinked_beer_user(chatid: int, userid: int, drinked: float):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM `beer` WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )
            result = await cursor.fetchone()

            if result is None or result == ():
                await create_beer_user(
                    cursor,
                    chatid,
                    userid,
                    last_drink=time.time(),
                    drinked=drinked
                )
                return

            await cursor.execute(
                """
UPDATE `beer`
SET drinkedtotal = drinkedtotal + %s, last_drink = %s WHERE chatid = %s AND userid = %s""",
                (drinked, time.time(), chatid, userid,)
            )

async def get_top_beer_users(chatid: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM `beer` WHERE chatid = %s ORDER BY drinkedtotal DESC LIMIT 10",
                (chatid,)
            )
            return await cursor.fetchall()

async def delete_from_beer(chatid: int, userid: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "DELETE FROM beer WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )

async def create_reputation_user(cursor, chatid, userid, reputation=0, last_add_time=0):
    await cursor.execute(
        """
INSERT INTO `reputation`
(chatid, userid, reputation, last_add_time)
VALUES (%s, %s, %s, %s)
""",
        (chatid, userid, reputation, last_add_time)
    )

    return cursor.lastrowid

async def increment_reputation_user(chatid, userid, author_userid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT n FROM `reputation` WHERE chatid = %s AND userid = %s",
                (chatid, author_userid,)
            )

            result = await cursor.fetchone()

            if result is None or result == {}:
                await create_reputation_user(
                    cursor,
                    chatid,
                    author_userid,
                    last_add_time=time.time()
                )
            else:
                await cursor.execute(
                    "UPDATE `reputation` SET last_add_time = %s WHERE n = %s",
                    (time.time(), result["n"],)
                )

            await cursor.execute(
                "SELECT n FROM `reputation` WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )
            result = await cursor.fetchone()

            if result is None or result == {}:
                await create_reputation_user(cursor, chatid, userid, reputation=1)
            else:
                await cursor.execute(
                    "UPDATE `reputation` SET reputation = reputation + 1 WHERE n = %s",
                    (result["n"],)
                )

async def decrement_reputation_user(chatid, userid, author_userid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT n FROM `reputation` WHERE chatid = %s AND userid = %s",
                (chatid, author_userid,)
            )

            result = await cursor.fetchone()

            if result is None or result == {}:
                await create_reputation_user(
                    cursor,
                    chatid,
                    author_userid,
                    last_add_time=time.time()
                )
            else:
                await cursor.execute(
                    "UPDATE `reputation` SET last_add_time = %s WHERE n = %s",
                    (time.time(), result["n"],)
                )

            await cursor.execute(
                "SELECT n FROM `reputation` WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )
            result = await cursor.fetchone()

            if result == None or result == {}:
                await create_reputation_user(
                    cursor,
                    chatid,
                    userid,
                    reputation=-1
                )
            else:
                await cursor.execute(
                    "UPDATE `reputation` SET reputation = reputation - 1 WHERE n = %s",
                    (result["n"],)
                )

async def get_reputation_user(chatid, userid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM `reputation` WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )
            result = await cursor.fetchone()

            if result == None or result == {}:
                row = await create_reputation_user(
                    cursor,
                    chatid,
                    userid,
                    last_add_time=0
                )
                return {
                    "n": row,
                    "chatid": chatid,
                    "userid": userid,
                    "reputation": 0,
                    "last_add_time": 0
                }
            else:
                return result

async def get_theme(themeid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM themes WHERE id = %s", (themeid,))
            return await cursor.fetchone()

@cached(THEME_CACHE)
async def get_group_theme(chatid):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT theme_id FROM group_settings WHERE chatid = %s",
                (chatid,)
            )
            result = await cursor.fetchone()
            if result is None:
                await create_group(cursor, chatid)
                await cursor.execute("SELECT * FROM themes WHERE id = 0")
                return await cursor.fetchone()

            logger.info(result)
            await cursor.execute(
                "SELECT * FROM themes WHERE id = %s",
                (result.get("theme_id", 0),)
            )

            return await cursor.fetchone()

async def set_group_theme(chatid, theme):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT id FROM group_settings WHERE chatid = %s",
                (chatid,)
            )
            result = await cursor.fetchone()
            if result == None or result == ():
                await create_group(cursor, chatid,)

            await cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM themes WHERE id = %s) AS row_exists",
                (theme,)
            )
            result = await cursor.fetchone()

            if not result["row_exists"]:
                raise KeyError("Нет темы с указанным id")

            await cursor.execute(
                "UPDATE group_settings SET theme_id = %s WHERE chatid = %s",
                (theme, chatid,)
            )

async def get_themes():
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM themes")
            return await cursor.fetchall()

async def create_group_user_settings(chatid: str | int, userid: str | int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "INSERT INTO user_settings (chatid, userid) VALUES (%s, %s)",
                (chatid, userid,)
            )

async def set_group_user_description(chatid: str | int, userid: str | int, description: str):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT id FROM user_settings WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )
            result = await cursor.fetchone()
            if not result:
                await create_group_user_settings(chatid, userid)
            await cursor.execute(
                "UPDATE user_settings SET description = %s WHERE chatid = %s AND userid = %s",
                (description, chatid, userid)
            )

async def get_group_user_description(chatid: str | int, userid: str | int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT description FROM user_settings WHERE chatid = %s AND userid = %s",
                (chatid, userid,)
            )
            result = await cursor.fetchone()
            if not result:
                await create_group_user_settings(chatid, userid)
                await cursor.execute(
                    "SELECT description FROM user_settings WHERE chatid = %s AND userid = %s",
                    (chatid, userid,)
                )
                result = await cursor.fetchone()
            return result["description"]

async def add_group_user_award(
        chatid: int,
        from_userid: int,
        to_userid: int,
        level: int,
        text: str
    ):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
INSERT INTO awards (chat_id, from_user_id, to_user_id, level, text)
VALUES (%s, %s, %s, %s, %s)""",
                (chatid, from_userid, to_userid, level, text,)
            )

async def get_group_user_awards(chatid: int, userid: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
SELECT * FROM awards WHERE chat_id = %s AND to_user_id = %s""",
                (chatid, userid,)
            )
            return await cursor.fetchall()
