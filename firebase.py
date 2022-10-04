import firebase_admin
from firebase_admin import db
from constants import DATABASE_URL, FIREBASE_CERTIFICATE


GREYLIST_KEY = "greylist"
USERS_KEY = "users"


DEFAULT_LIMIT = 5


cred_obj = firebase_admin.credentials.Certificate(FIREBASE_CERTIFICATE)
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL': DATABASE_URL
})


def get_bot_info(bot_id):
    ref = db.reference(f"/{bot_id}", default_app)
    result: dict = ref.get()
    return result


def set_bot_info(bot_id, bot_info):
    parent_ref = db.reference(f"/", default_app)
    parent_result: dict = parent_ref.get()

    parent_result[bot_id] = bot_info
    parent_ref.update(parent_result)
    return bot_info


def get_chat_info(bot_id, chat_id):
    bot_info = get_bot_info(bot_id)
    chat_id = str(chat_id)
    if bot_info and chat_id in bot_info:
        return bot_info[chat_id]


def set_chat_info(bot_id, chat_id, chat_info):
    bot_info = get_bot_info(bot_id)
    chat_id = str(chat_id)
    if bot_info:
        bot_info[chat_id] = chat_info
    else:
        bot_info = {chat_id: chat_info}
    set_bot_info(bot_id, bot_info)
    return chat_info


def get_chat_limits(bot_id, chat_id):
    chat_info = get_chat_info(bot_id, chat_id)
    if chat_info:
        return chat_info[GREYLIST_KEY]
    else:
        return None


def set_chat_limits(bot_id, chat_id, phrase, count):
    chat_info = get_chat_info(bot_id, chat_id)
    if chat_info and GREYLIST_KEY in chat_info:
        chat_info[GREYLIST_KEY][phrase] = count
    elif chat_info:
        chat_info[GREYLIST_KEY] = {phrase: count}
    else:
        chat_info = {
            GREYLIST_KEY: {phrase: count},
            USERS_KEY: None
        }
    set_chat_info(bot_id, chat_id, chat_info)
    return


def get_user_info(bot_id, chat_id, user_id):
    user_id = str(user_id)
    chat_info = get_chat_info(bot_id, chat_id)
    if chat_info and USERS_KEY in chat_info:
        if chat_info[USERS_KEY]:
            if user_id in chat_info[USERS_KEY]:
                return chat_info[USERS_KEY][user_id]
            else:
                return [None, 0]
    else:
        return [None, 0]


def set_user_info(bot_id, chat_id, user_id, phrase_and_count):
    user_id = str(user_id)
    chat_info = get_chat_info(bot_id, chat_id)
    if chat_info:
        if USERS_KEY in chat_info:
            chat_info[USERS_KEY][user_id] = phrase_and_count
        else:
            chat_info[USERS_KEY] = {user_id: phrase_and_count}
    else:
        chat_info = {
            GREYLIST_KEY: {"phrase for test bot": DEFAULT_LIMIT},
            USERS_KEY: {user_id: phrase_and_count}
        }
    set_chat_info(bot_id, chat_id, chat_info)
    return phrase_and_count


def del_user_info(bot_id, chat_id, user_id):
    user_id = str(user_id)
    chat_info = get_chat_info(bot_id, chat_id)
    if chat_info:
        if chat_info[USERS_KEY]:
            del chat_info[USERS_KEY][user_id]
            if not chat_info[USERS_KEY]:
                del chat_info[USERS_KEY]
    set_chat_info(bot_id, chat_id, chat_info)
    return
