from html import escape
import traceback

from aiogram import types, Bot

import config

text2wingdings_dict = {
    'q': '❑', 'w': '⬥', 'e': '♏', 'r': '❒', 't': '⧫', 'y': '⍓', 'u': '◆', 'i': '♓',
    'o': '□', 'p': '◻', 'a': '♋', 's': '⬧', 'd': '♎', 'f': '♐', 'g': '♑', 'h': '♒',
    'j': 'j', 'k': '&', 'l': '●', 'z': '⌘', 'x': '⌧', 'c': '♍', 'v': '❖', 'b': '♌',
    'n': '■', 'm': '❍', 'Q': '✈', 'W': '🕈', 'E': '☜', 'R': '☼', 'T': '❄', 'Y': '✡',
    'U': '🕆', 'I': '✋', 'O': '⚐', 'P': '🏱', 'A': '✌', 'S': '💧', 'D': '👎', 'F': '☞',
    'G': '☝', 'H': '☟', 'J': '☺', 'K': '😐', 'L': '☹', 'Z': '☪', 'X': '✠', 'C': '👍',
    'V': '✞', 'B': '👌', 'N': '☠', 'M': '💣', ',': '📪', '.': '📬', '1': '📂', '2': '📄',
    '3': '🗏', '4': '🗐', '5': '🗄', '6': '⌛', '7': '🖮', '8': '🖰', '9': '🖲', '0': '📁',
    '#': '✁', '$': '👓', '_': '♉', '&': '🕮', '-': '📫', '+': '🖃', '(': '☎', ')': '✆',
    '/': '📭', '*': '🖂', '"': '✂', "'": '🕯', ':': '🖳', ';': '🖴', '!': '✏', '?': '✍',
    '~': '❞', '`': '♊', '|': '✿', '•': '•', '÷': '÷', '×': '×', '§': '§', '£': '£',
    '¢': '¢', '€': '€', '¥': '¥', '^': '♈', '°': '°', '=': '🖬', '{': '❀', '}': '❝',
    '\\': 'ॐ', '%': '🕭', '©': '©', '®': '®', '™': '™', '[': '☯', ']': '☸', '<': '🖫', '>': '✇'
}

windings2text_dict = {
    '❑': 'q', '⬥': 'w', '♏': 'e', '❒': 'r', '⧫': 't', '⍓': 'y', '◆': 'u', '♓': 'i',
    '□': 'o', '◻': 'p', '♋': 'a', '⬧': 's', '♎': 'd', '♐': 'f', '♑': 'g', '♒': 'h',
    'j': 'j', '&': 'k', '●': 'l', '⌘': 'z', '⌧': 'x', '♍': 'c', '❖': 'v', '♌': 'b',
    '■': 'n', '❍': 'm', '✈': 'Q', '🕈': 'W', '☜': 'E', '☼': 'R', '❄': 'T', '✡': 'Y',
    '🕆': 'U', '✋': 'I', '⚐': 'O', '🏱': 'P', '✌': 'A', '💧': 'S', '👎': 'D', '☞': 'F',
    '☝': 'G', '☟': 'H', '☺': 'J', '😐': 'K', '☹': 'L', '☪': 'Z', '✠': 'X', '👍': 'C',
    '✞': 'V', '👌': 'B', '☠': 'N', '💣': 'M', '📪': ',', '📬': '.', '📂': '1', '📄': '2',
    '🗏': '3', '🗐': '4', '🗄': '5', '⌛': '6', '🖮': '7', '🖰': '8', '🖲': '9', '📁': '0',
    '✁': '#', '👓': '$', '♉': '_', '🕮': '&', '📫': '-', '🖃': '+', '☎': '(', '✆': ')',
    '📭': '/', '🖂': '*', '✂': '"', '🕯': "'", '🖳': ':', '🖴': ';', '✏': '!', '✍': '?',
    '❞': '~', '♊': '`', '✿': '|', '•': '•', '÷': '÷', '×': '×', '§': '§', '£': '£',
    '¢': '¢', '€': '€', '¥': '¥', '♈': '^', '°': '°', '🖬': '=', '❀': '{', '❝': '}',
    'ॐ': '\\', '🕭': '%', '©': '©', '®': '®', '™': '™', '☯': '[', '☸': ']', '🖫': '<', '✇': '>'
}

def text2windings(text):
    result = []
    for char in text:
        if char in text2wingdings_dict:
            result.append(text2wingdings_dict[char])
        else:
            result.append(char)
    return ''.join(result)

def windings2text(text):
    result = []
    for char in text:
        if char in windings2text_dict:
            result.append(windings2text_dict[char])
        else:
            result.append(char)
    return ''.join(result)

async def inline_query(inline_query: types.InlineQuery, bot: Bot):
    try:
        query = inline_query.query.split()

        if query[0] == "snowgrave":
            fullname = f"{inline_query.from_user.first_name} {inline_query.from_user.last_name or ''}".strip()

            result = types.InlineQueryResultArticle(
                id="1",
                title="Отправить",
                input_message_content=types.InputTextMessageContent(
                    message_text=f"""
❄️ {fullname} хочет сделать snowgrave
"""
                ),
                description=f"""
❄️ {fullname} хочет сделать snowgrave
""",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="❤️ Proceed",
                                callback_data=f"snowgraveyes:{inline_query.from_user.id}"
                            ),
                            types.InlineKeyboardButton(
                                text="Do not",
                                callback_data=f"inlineno:{inline_query.from_user.id}"
                            )
                        ]
                    ]
                )
            )

            await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
            return True
        elif query[0] == "invite_to_tea":
            fullname = f"{inline_query.from_user.first_name} {inline_query.from_user.last_name or ''}".strip()

            result = types.InlineQueryResultArticle(
                id="1",
                title="Отправить",
                input_message_content=types.InputTextMessageContent(
                    message_text=f"""
{fullname} хочет пригласить вас на чай
"""
                ),
                description=f"""
{fullname} хочет пригласить вас на чай
""",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Согласиться",
                                callback_data=f"teayes:{inline_query.from_user.id}"
                            ),
                            types.InlineKeyboardButton(
                                text="Отказаться",
                                callback_data=f"inlineno:{inline_query.from_user.id}"
                            )
                        ]
                    ]
                )
            )

            await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
            return True
        elif query[0] == "text2windings":
            if len(query) == 1:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="⚠️ Введите текст на английском для перевода в Windings",
                    input_message_content=types.InputTextMessageContent(
                        message_text="⚠️ Введите текст на английском для перевода в Windings"
                    )
                )
                await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                return True

            converted = text2windings(" ".join(query[1:]))

            result = types.InlineQueryResultArticle(
                id="1",
                title="Отправить",
                input_message_content=types.InputTextMessageContent(
                    message_text=converted
                ),
                description=converted[:300]
            )

            await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
            return True
        elif query[0] == "windings2text":
            if len(query) == 1:
                result = types.InlineQueryResultArticle(
                    id="1",
                    title="⚠️ Введите текст на Windings для перевода в текст",
                    input_message_content=types.InputTextMessageContent(
                        message_text="⚠️ Введите текст на Windings для перевода в текст"
                    )
                )
                await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
                return True

            converted = windings2text(" ".join(query[1:]))

            result = types.InlineQueryResultArticle(
                id="1",
                title="Отправить",
                input_message_content=types.InputTextMessageContent(
                    message_text=converted
                ),
                description=converted[:300]
            )

            await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
            return True
        else:
            return False
    except:
        result = types.InlineQueryResultArticle(
            id="1",
            title="⚠️ Произошла ошибка, попробуйте позже",
            input_message_content=types.InputTextMessageContent(
                message_text="⚠️ Произошла ошибка, попробуйте позже"
            ),
        )
        await bot.answer_inline_query(inline_query.id, results=[result], cache_time=1)
        await bot.send_message(
            config.DEV_ADMIN_USERID,
            f"⚠️ Ошибка в inline_query. \
Traceback: \
<pre>{escape(traceback.format_exc()[-500:])}</pre>",
            parse_mode='HTML'
        )

async def callback_query(call: types.CallbackQuery, bot: Bot):
    if call.data.startswith("snowgraveyes"):
        _, user = call.data.split(":")

        if call.from_user.id == int(user):
            await call.answer("⚠️ Это не тебе", show_alert=True)
            return

        fullname = f"{call.from_user.first_name} {call.from_user.last_name or ''}".strip()

        await bot.edit_message_text(
            f"❄️ Вы заморозили <a href=\"tg://user?id={user}\">{escape(fullname)}</a>. ❤️ Proceed",
            inline_message_id=call.inline_message_id,
            parse_mode="HTML"
        )
    elif call.data.startswith("inlineno"):
        _, user = call.data.split(":")

        if call.from_user.id == int(user):
            await call.answer("⚠️ Это не тебе", show_alert=True)
            return

        fullname = f"{call.from_user.first_name} {call.from_user.last_name or ''}".strip()

        await bot.edit_message_text(
            f"❌ <a href=\"tg://user?id={user}\">{escape(fullname)}</a> отказал(ась)",
            inline_message_id=call.inline_message_id,
            parse_mode="HTML"
        )
