import logging

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackContext, MessageHandler)
from telegram.ext.filters import TEXT, COMMAND

from constants import TELEGRAM_TOKEN


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Enable logging
logger = logging.getLogger(__name__)


async def echo(update: Update, context: CallbackContext) -> None:
    await update.effective_message.reply_text(update.effective_message.text)


def get_tg_application():
    tg_application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_application.add_handler(MessageHandler(TEXT & ~COMMAND, echo))
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
