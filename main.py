import logging
import re

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackContext, MessageHandler)
from telegram.ext.filters import TEXT, COMMAND, ALL

from constants import TELEGRAM_TOKEN, BLOCK_USERS_WITH_NAMES_REGEXP, GREY_PHRASES_LIST
from firebase import get_user_info, set_user_info, get_chat_limits, del_user_info


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
                    await update.effective_message.reply_text(f'ban for you: {full_name}')
                    await context.bot.banChatMember(chat_id=chat_id, user_id=member_id)
                    break
        except Exception as e:
            await update.effective_message.reply_text(f'failed: {e}')


async def calculate_messages(update: Update, context: CallbackContext) -> None:
    text = update.effective_message.text
    text_lower = (text or '').lower()
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    user_id = update.effective_message.from_user.id

    text_like_pattern = False
    latest_pattern, count = get_user_info(bot_id, chat_id, user_id)

    for pattern in GREY_PHRASES_LIST:
        pattern_lower = pattern.lower()
        await update.effective_message.reply_text(f"We are checking this message ({text_lower}) with pattern: {pattern_lower}")
        if text_lower == pattern_lower:
            text_like_pattern = True
            grey_phrases_limit = get_chat_limits(bot_id, chat_id)

            await update.effective_message.reply_text(
                f"Limit: {grey_phrases_limit}, your score was: {count} ({type(count)}). Be careful!")
            await update.effective_message.reply_text(
                f"Latest phrase: {latest_pattern}, pattern: {pattern_lower}")

            if latest_pattern != pattern_lower:
                count = 1
            else:
                count += 1

            if count > 1:
                await update.effective_message.reply_text(
                    f"1st step of refreshing info about you")
                del_user_info(bot_id, chat_id, user_id)

            if grey_phrases_limit <= count:
                await context.bot.banChatMember(chat_id=chat_id, user_id=user_id)
                await update.effective_message.reply_text(f"I'm sorry (not). Your behaviour similar to spam-accounts, ban!")
            set_user_info(bot_id, chat_id, user_id, [pattern_lower, count])
            break
    if not text_like_pattern:
        del_user_info(bot_id, chat_id, user_id)


async def filter_by_name_and_messages(update: Update, context: CallbackContext) -> None:
    await check_and_ban_new_members(update, context)
    await calculate_messages(update, context)


def get_tg_application():
    tg_application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_application.add_handler(MessageHandler(filters=ALL, callback=filter_by_name_and_messages))
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
