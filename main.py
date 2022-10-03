import logging
import re

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackContext, MessageHandler)
from telegram.ext.filters import TEXT, COMMAND, ALL

from constants import TELEGRAM_TOKEN, BLOCK_USERS_WITH_NAMES_REGEXP


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Enable logging
logger = logging.getLogger(__name__)


async def check_and_ban_new_members(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_message.chat_id
    new_chat_members = update.effective_message.new_chat_members
    for new_chat_member in new_chat_members:
        member_id = new_chat_member.id
        full_name = new_chat_member.full_name
        try:
            for pattern in BLOCK_USERS_WITH_NAMES_REGEXP:
                if re.fullmatch(pattern, full_name):
                    await context.bot.banChatMember(chat_id=chat_id, user_id=member_id)
                    break
        except Exception as e:
            await update.effective_message.reply_text(f'failed: {e}')


def get_tg_application():
    tg_application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_application.add_handler(MessageHandler(filters=ALL, callback=check_and_ban_new_members))
    return tg_application


app = FastAPI()
tg_application = get_tg_application()


@app.post("/webhook")
async def webhook_handler(req: Request):
    data = await req.json()

    try:
        await tg_application.initialize()
        update = Update.de_json(data, tg_application.bot)
        await tg_application.process_update(update)
    except Exception as e:
        print(f'Webhook error: {e}')
