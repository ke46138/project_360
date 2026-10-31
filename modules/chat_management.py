import asyncio
from html import escape

from aiogram import Router, types, Bot
from aiogram.filters import Command

import config
from modules import async_tasks
from modules import auth
from modules import botdebug as d
from modules import filters
from modules import mysql_adapter as sql
from modules import urlfilter
from modules import utils

router = Router()

@router.message(Command("pin"))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=100)
async def pin_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply_to_message.pin()
        await message.react([types.ReactionTypeEmoji(emoji='👍')])
        asyncio.create_task(async_tasks.delete_msg(message, bot))
    else:
        await message.reply("⚠️ Вы должны ответить на сообщение, которое хотите закрепить")

@router.message(Command("unpin"))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=100)
async def unpin_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply_to_message.unpin()
        await message.react([types.ReactionTypeEmoji(emoji='👍')])
        asyncio.create_task(async_tasks.delete_msg(message, bot))
    else:
        await message.reply("⚠️ Вы должны ответить на сообщение, которое хотите открепить")

@router.message(Command("ping_admins"))
@d.bugreport
@filters.cooldown(ctime=300)
@filters.only_groups
async def ping_admins(message: types.Message, bot: Bot):
    """Команда для функции 'Созвать админов'"""
    admins = await sql.get_group_admins(message.chat.id, bot)

    msg = ""

    for i in admins:
        if i[1] >= 100:
            admin = await bot.get_chat_member(message.chat.id, i[0])
            msg += f"{utils.wrap_user_link(admin.user.full_name, i[0])} "

    if msg == "":
        await message.reply("⚠️ Админов нет")
    else:
        await message.reply(msg, parse_mode="HTML")

@router.message(Command("admins"))
@d.bugreport
@filters.only_groups
@filters.cooldown
async def admins(message: types.Message, bot: Bot):
    """Генерирует и отправляет список админов"""
    bot_admins = await sql.get_group_admins(message.chat.id, bot)
    tg_admins = await bot.get_chat_administrators(message.chat.id)

    strings = []

    bot_admin_ids = {uid for uid, _ in bot_admins}

    elites = [a.user.id for a in tg_admins if a.user.id not in bot_admin_ids]

    devs = [uid for uid, lvl in bot_admins if lvl == 255]
    admins = [uid for uid, lvl in bot_admins if lvl == 200]
    moders = [uid for uid, lvl in bot_admins if 100 <= lvl < 200]
    elites += [uid for uid, lvl in bot_admins if lvl < 100]

    if devs:
        strings.append("<b>Разработчики/создатели:</b>")
        for n in devs:
            user = await bot.get_chat_member(message.chat.id, n)
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            strings.append(utils.wrap_user_link(fullname, n))
    if admins:
        strings.append("<b>Главные админы:</b>")
        for n in admins:
            user = await bot.get_chat_member(message.chat.id, n)
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            strings.append(utils.wrap_user_link(fullname, n))
    if moders:
        strings.append("<b>Модераторы:</b>")
        for n in moders:
            user = await bot.get_chat_member(message.chat.id, n)
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            strings.append(utils.wrap_user_link(fullname, n))
    if elites:
        strings.append("<b>Элиты:</b>")
        for n in elites:
            user = await bot.get_chat_member(message.chat.id, n)
            fullname = f"{user.user.first_name} {user.user.last_name or ''}".strip()
            strings.append(utils.wrap_user_link(fullname, n))

    if strings == [] or strings is None:
        strings = ["⚠️ Список админов пуст"]

    await message.reply("\n".join(strings), parse_mode='HTML', disable_notification=True)

@router.message(Command('set_rules'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def set_rules_command(message: types.Message, bot: Bot):
    rules = message.text.split(' ', 1)[1] if ' ' in message.text else "⚠️ Правила отсутствуют"

    await sql.update_group_rules(message.chat.id, rules)
    await message.react([types.ReactionTypeEmoji(emoji='👍')])

@router.message(Command('disable_urlfilter'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def disable_urlfilter_command(message: types.Message, bot: Bot):
    await sql.update_urlfilter_enabled(message.chat.id, False)
    urlfilter.set_cached_status(message.chat.id, False)
    await message.reply("✅ Фильтр ссылок выключен.")

@router.message(Command('enable_urlfilter'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def enable_urlfilter_command(message: types.Message, bot: Bot):
    await sql.update_urlfilter_enabled(message.chat.id, True)
    urlfilter.set_cached_status(message.chat.id, True)
    await message.reply("✅ Фильтр ссылок включён.")

@router.message(Command('add_filter_link'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def add_filter_link_command(message: types.Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply(
            "⚠️ Укажите домен. Пример: /add_filter_link example.com",
            parse_mode="HTML"
        )
        return

    raw_domain = args[1].strip().split()[0]
    domain = urlfilter.normalize_domain(raw_domain)
    if not domain or "." not in domain:
        await message.reply(
            "⚠️ Некорректный домен. Пример: example.com",
            parse_mode="HTML"
        )
        return

    added = await sql.add_group_allowed_url(message.chat.id, domain)
    if added:
        urlfilter.invalidate_domains_cache(message.chat.id)
        await message.reply(
            f"✅ Домен {escape(domain)} успешно добавлен в список разрешённых",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            f"ℹ️ Домен {escape(domain)} уже находится в списке разрешённых",
            parse_mode="HTML"
        )

@router.message(Command('del_filter_link', 'remove_filter_link'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def del_filter_link_command(message: types.Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply(
            "⚠️ Укажите домен для удаления. Пример: /del_filter_link example.com",
            parse_mode="HTML"
        )
        return

    raw_domain = args[1].strip().split()[0]
    domain = urlfilter.normalize_domain(raw_domain)
    if not domain:
        await message.reply(
            "⚠️ Некорректный домен",
            parse_mode="HTML"
        )
        return

    removed = await sql.remove_group_allowed_url(message.chat.id, domain)
    if removed:
        urlfilter.invalidate_domains_cache(message.chat.id)
        await message.reply(
            f"✅ Домен {escape(domain)} удалён из списка разрешённых",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            f"⚠️ Домен {escape(domain)} не найден в списке разрешённых доменов",
            parse_mode="HTML"
        )

@router.message(Command('filter_links', 'filter_link_list', 'list_filter_links'))
@d.bugreport
@filters.only_groups
async def list_filter_links_command(message: types.Message, bot: Bot):
    custom_domains = await sql.get_group_allowed_urls(message.chat.id)

    lines = ["<b>🌐 Разрешённые домены для ссылок:</b>\n"]
    if custom_domains:
        for d_name in sorted(custom_domains):
            lines.append(f"    {escape(d_name)}")
    else:
        lines.append("⚠️ Разрешённые домены не добавлены")

    await message.reply("\n".join(lines), parse_mode='HTML')

@router.message(Command('set_hello'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=100)
async def set_hello_command(message: types.Message, bot: Bot):
    _, hellotext = message.text.split(maxsplit=1)

    await sql.update_group_hello(message.chat.id, hellotext)

    await message.react([types.ReactionTypeEmoji(emoji='👍')])

@router.message(Command('toggle_hello'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=100)
async def toggle_hello_command(message: types.Message, bot: Bot):
    result = await sql.toggle_group_hello(message.chat.id)

    if result:
        await message.reply("✅ Приветствие включено")
    else:
        await message.reply("🚫 Приветствие выключено")

@router.message(Command('set_admin'))
@d.bugreport
@filters.only_groups
@auth.require_auth(level=200)
async def set_admin_command_v2(message: types.Message, bot: Bot):
    if message.reply_to_message:
        if message.reply_to_message.sender_chat:
            user_id = message.reply_to_message.sender_chat.id
        elif message.reply_to_message.from_user:
            user_id = message.reply_to_message.from_user.id

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply("⚠️ Вам нужно указать ранг: главный админ, модератор, никто")
            return

        if args[1] == "главный админ":
            args[1] = 200
        elif args[1] == "модератор":
            args[1] = 100
        elif args[1] == "никто":
            args[1] = 0
        else:
            await message.reply("⚠️ Не знаю такого ранга")
            return

        admins = await sql.get_group_admins(message.chat.id, bot)
        index = 0
        level = 0
        isUserAdmin = False
        for i in admins:
            if user_id == i[0]:
                isUserAdmin = True
                level = i[1]
                break
            index += 1

        if isUserAdmin:
            if args[1] == 0:
                admins.remove([user_id, level])
            else:
                admins[index][1] = args[1]
        else:
            if args[1] != 0:
                admins.append([user_id, args[1]])
            else:
                await message.reply("⚠️ Пользователь не является админом")
                return

        await sql.set_group_admins(message.chat.id, admins)

        await message.react([types.ReactionTypeEmoji(emoji='👍')])
    else:
        await message.reply("⚠️ Вам нужно ответить на сообщения пользователя, которого хотите сделать админом")

