import traceback
from aiogram import Router, types, F, Bot

from modules import botdebug as d
import config

router = Router()

@router.message(F.sender_chat.id == config.CHANNEL_ID)
async def advert(message: types.Message, bot: Bot):
    try:
        await message.unpin()
        await message.reply(config.ADVERT_TEXT, parse_mode='HTML', disable_web_page_preview=True)
    except:
        await d.send_view_traceback(message, traceback.format_exc(), bot)