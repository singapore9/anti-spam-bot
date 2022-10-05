import logging
import re

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackContext, MessageHandler, CommandHandler)
from telegram.ext.filters import TEXT, COMMAND

from constants import TELEGRAM_TOKEN
from commands import (users_pattern_add, users_pattern_show, users_pattern_remove,
                      greylist_phrase_add, greylist_phrase_show, greylist_phrase_remove)
from firebase import get_user_info, set_user_info, get_chat_limits, del_user_info, get_chat_users_patterns, DEFAULT_LIMIT


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Enable logging
logger = logging.getLogger(__name__)


async def check_and_ban_new_members(update: Update, context: CallbackContext) -> None:
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    new_chat_members = update.effective_message.new_chat_members
    block_user_patterns = list((get_chat_users_patterns(bot_id, chat_id) or dict()).values())
    for new_chat_member in new_chat_members:
        member_id = new_chat_member.id
        full_name = new_chat_member.full_name
        try:
            for pattern in block_user_patterns:
                if re.fullmatch(pattern, full_name):
                    await context.bot.banChatMember(chat_id=chat_id, user_id=member_id)
                    break
        except Exception as e:
            pass


async def calculate_messages(update: Update, context: CallbackContext) -> None:
    text = update.effective_message.text
    text_lower = (text or '').lower()
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    user_id = update.effective_message.from_user.id

    text_like_pattern = False
    latest_pattern, count = get_user_info(bot_id, chat_id, user_id)
    grey_phrases_limits = get_chat_limits(bot_id, chat_id)
    grey_phrases = list((grey_phrases_limits or dict()).keys())

    for pattern in grey_phrases:
        pattern_lower = pattern.lower()
        if text_lower == pattern_lower:
            text_like_pattern = True
            specific_limit = (grey_phrases_limits or dict()).get(pattern_lower, DEFAULT_LIMIT)

            if latest_pattern != pattern_lower:
                count = 1
            else:
                count += 1

            if count > 1:
                del_user_info(bot_id, chat_id, user_id)

            if specific_limit <= count:
                await context.bot.banChatMember(chat_id=chat_id, user_id=user_id)
            set_user_info(bot_id, chat_id, user_id, [pattern_lower, count])
            break
    if not text_like_pattern:
        del_user_info(bot_id, chat_id, user_id)


async def filter_by_name_and_messages(update: Update, context: CallbackContext) -> None:
    await check_and_ban_new_members(update, context)
    await calculate_messages(update, context)


def get_tg_application():
    tg_application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_application.add_handler(MessageHandler(filters=TEXT & ~COMMAND, callback=filter_by_name_and_messages))
    tg_application.add_handler(CommandHandler('users_pattern_add', users_pattern_add))
    tg_application.add_handler(CommandHandler('users_pattern_show', users_pattern_show))
    tg_application.add_handler(CommandHandler('users_pattern_remove', users_pattern_remove))
    tg_application.add_handler(CommandHandler('greylist_phrase_add', greylist_phrase_add))
    tg_application.add_handler(CommandHandler('greylist_phrase_show', greylist_phrase_show))
    tg_application.add_handler(CommandHandler('greylist_phrase_remove', greylist_phrase_remove))
    # users_pattern_add "\s*\w\("
    # users_pattern_show
    # users_pattern_remove "\s*\w\s("
    # greylist_phrase_add 5 hello
    # greylist_phrase_show
    # greylist_phrase_remove hello
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
