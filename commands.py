from telegram import Update
from telegram.ext import CallbackContext

from firebase import (get_chat_limits, set_chat_limits, del_chat_limits,
                      get_chat_users_patterns, set_chat_users_patterns, del_chat_users_patterns)


async def users_pattern_show(update: Update, context: CallbackContext) -> None:
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    user_id = update.effective_message.from_user.id

    user_patterns = list((get_chat_users_patterns(bot_id, chat_id) or dict()).values())
    user_patterns_str = '\n'.join([f"...({user_pattern})..." for user_pattern in user_patterns])

    await update.message.reply_text(f"Patterns are:\n{user_patterns_str}")


async def greylist_phrase_show(update: Update, context: CallbackContext) -> None:
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    user_id = update.effective_message.from_user.id

    greylist_phrases = get_chat_limits(bot_id, chat_id) or dict()
    greylist_phrases_str = '\n'.join([f"...({greylist_phrase}) for {limit} times..." for greylist_phrase, limit in greylist_phrases.items()])

    await update.message.reply_text(f"Phrases are:\n{greylist_phrases_str}")


async def users_pattern_remove(update: Update, context: CallbackContext) -> None:
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    user_pattern = (update.effective_message.text or '').strip().split(' ', maxsplit=1)[-1]
    user_id = update.effective_message.from_user.id

    if user_pattern:
        user_patterns = list((get_chat_users_patterns(bot_id, chat_id) or dict()).values())
        if user_pattern in user_patterns:
            del_chat_users_patterns(bot_id, chat_id, user_pattern)

    await update.message.reply_text(f"Pattern \"{user_pattern}\" was removed from list of blocked usernames")


async def greylist_phrase_remove(update: Update, context: CallbackContext) -> None:
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    phrase = (update.effective_message.text or '').strip().split(' ', maxsplit=1)[-1]
    user_id = update.effective_message.from_user.id

    if phrase:
        greylist_phrases_with_limits = (get_chat_limits(bot_id, chat_id) or dict())
        if phrase in greylist_phrases_with_limits:
            del_chat_limits(bot_id, chat_id, phrase)

    await update.message.reply_text(f"Phrase \"{phrase}\" was removed from greylist")


async def users_pattern_add(update: Update, context: CallbackContext) -> None:
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    command_args = (update.effective_message.text or '').strip().split(' ', maxsplit=1)
    if len(command_args) == 1:
        await update.message.reply_text(f"This command requires 1 argument")
        return

    user_pattern = command_args[-1]
    user_id = update.effective_message.from_user.id

    if user_pattern:
        user_patterns = list((get_chat_users_patterns(bot_id, chat_id) or dict()).values())
        if user_pattern in user_patterns:
            await update.message.reply_text(f"Pattern \"{user_pattern}\" is already in list of blocked usernames")
        else:
            set_chat_users_patterns(bot_id, chat_id, user_pattern)
            await update.message.reply_text(f"Pattern \"{user_pattern}\" was added in list of blocked usernames")
    else:
        await update.message.reply_text(f"Can't read pattern from command call")


async def greylist_phrase_add(update: Update, context: CallbackContext) -> None:
    bot_id = context.bot.id
    chat_id = update.effective_message.chat_id
    count_and_phrase = (update.effective_message.text or '').strip().split(' ', maxsplit=1)[-1]
    user_id = update.effective_message.from_user.id

    if count_and_phrase:
        if len(count_and_phrase.split(' ', maxsplit=1)) != 2:
            await update.message.reply_text(f"Command should be called with NUMBER and PHRASE.\n"
                                            f"For example: /command 12 buy crypto")
        else:
            count, phrase = count_and_phrase.split(' ', maxsplit=1)
            try:
                count = int(count)
                if count < 1:
                    raise ValueError('...not positive ')
            except ValueError:
                count = -1
                await update.message.reply_text("1st argument of command is not a positive number")
            phrase = phrase.strip()
            if not phrase:
                await update.message.reply_text("2nd argument of command is empty")
            if count > 0 and phrase:
                set_chat_limits(bot_id, chat_id, phrase, count)
                await update.message.reply_text(f"Phrase \"{phrase}\" was added into greylist with limit as {count} repeats.")
