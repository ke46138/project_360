from aiogram import Router, types, Bot
from aiogram.filters import Command
from petrovich.enums import Case

from modules import botdebug as d
from modules import filters
from modules import utils

router: Router = Router()

@router.message(Command('kick'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def kick_command(message: types.Message, bot: Bot):
    """Пнуть пользователя"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" пнул(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите пнуть")

@router.message(Command('sword'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def sword_command(message: types.Message, bot: Bot):
    """Ударить мечом пользователя"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" ударил(а) мечом "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите ударить мечом")

@router.message(Command('rpg'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def kaboom_command(message: types.Message, bot: Bot):
    """РПГ"""
    if message.from_user.id != 1312172800:
        await message.reply("⚠️ Только для Ральзея!")
        return
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_user_link(message.from_user.full_name, message.from_user.id)}"
            f" выстрелил из рпг и взорвал "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя, в которого хотите выстрелить из рпг"
        )

@router.message(Command('pat'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def pat_command(message: types.Message, bot: Bot):
    """Погладить пользователя"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" погладил(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите погладить")

@router.message(Command('handshake'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def handshake_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" пожал(а) руку "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True, case=Case.DATIVE)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которому хотите пожать руку")

@router.message(Command('bite'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def bite_command(message: types.Message, bot: Bot):
    """Укусить пользователя"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" укусил(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите укусить")

@router.message(Command('slap'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def slap_command(message: types.Message, bot: Bot):
    """Дать пощёчину пользователю"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" дал(а) пощёчину "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True, case=Case.DATIVE)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которому хотите дать пощёчину")

@router.message(Command('kiss'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def kiss_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" поцеловал(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите поцеловать")

@router.message(Command('ak47'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def ak47_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" расстрелял(а) из АК-47 "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя, которого хотите расстрелять из АК-47"
        )

@router.message(Command('kill'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def kill_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" убил(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите убить")

@router.message(Command('kidnap'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def kidnap_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" похитил(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите похитить")

@router.message(Command('feed'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def feed_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" покормил(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите покормить")

@router.message(Command('tapok'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def tapok_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" ударил(а) тапком "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя, которого хотите ударить тапком"
        )

@router.message(Command('hug'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def hug_command(message: types.Message, bot: Bot):
    """Обнять пользователя"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" обнял(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите обнять")

@router.message(Command('laugh'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def laugh_command(message: types.Message, bot: Bot):
    """Посмеяться над пользователем"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" посмеялся(лась) над "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True, case=Case.INSTRUMENTAL)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, над которым хотите посмеяться")

@router.message(Command('burn'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def burn_command(message: types.Message, bot: Bot):
    """Сжечь пользователя пользователем"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" сжёг/сожгла "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите сжечь")

@router.message(Command('invite_to_tea'))
@d.bugreport
@filters.cooldown
@filters.only_groups
async def invite_to_tea_command(message: types.Message, bot: Bot):
    """Пригласить на чай"""
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" пригласил(а) на чай "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя, которого хотите пригласить на чай"
        )

@router.message(Command('backstab'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def backstab_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" бэкстабнул(а) "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя, которого хотите бэкстабнуть"
        )

@router.message(Command('axe'))
@filters.cooldown
@filters.only_groups
async def axe_command(message: types.Message, bot: Bot):
    """Ударить секирой пользователя"""
    if message.from_user.id != 6196235410:
        await message.reply("⚠️ Только для Сьюзи!")
        return
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_user_link(message.from_user.full_name, message.from_user.id)}"
            f" ударил(а) секирой "
            f"{utils.wrap_user_link(
                message.reply_to_message.from_user.full_name,
                message.reply_to_message.from_user.id
            )}",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            "⚠️ Ответьте на сообщение пользователя, которого хотите ударить секирой"
        )

@router.message(Command('make_shawarma'))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def make_shawarma_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" сделал(а) шаурму из "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, из которого хотите сделать шаурму")

@router.message(Command("make_cartel_property"))
@d.bugreport
@filters.cooldown
@filters.only_groups
@filters.antidev
async def make_cartel_property_command(message: types.Message, bot: Bot):
    if message.reply_to_message:
        await message.reply(
            f"{utils.wrap_actor_link(message)}"
            f" сделал(а) собственностью картеля "
            f"{utils.wrap_actor_link(message.reply_to_message, incline=True)}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого хотите сделать собственностью картеля")
