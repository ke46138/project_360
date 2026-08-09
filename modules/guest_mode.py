from aiogram import Router, types, Bot

router = Router()

@router.guest_message()
async def guest_query(guest_query: types.Message, bot: Bot):
    await guest_query.answer_guest_query(
        types.InlineQueryResultArticle(
            id="1",
            title="title",
            input_message_content=types.InputTextMessageContent(
                message_text="""Message"""
            )
        )
    )
