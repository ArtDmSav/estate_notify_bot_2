from telegram import Update
from telegram.ext import ContextTypes

from config.data import ADMIN
from db.connect import get_last_10_estate_ids, get_estate_by_id, get_estate_by_group_id_and_msg_id


async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN:
        menu_text = """
        Меню администратора:
            /eid - get last 10 Estate.id Ex: + ''\n
            /msgid - get msg with Estate.id Ex: + ' 357'\n
            /groupid - get msg with group_id and msg_id Ex: + ' dom_com_cy 105200'\n
            /u_list - get user list\n
            """
        await update.message.reply_text(menu_text)
    else:
        await update.message.reply_text('Access ERROR')


async def get_last_10_eids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id == ADMIN:
        eids = await get_last_10_estate_ids()
        await update.message.reply_text(eids)
    else:
        await update.message.reply_text('Access ERROR')


async def get_estate_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN:

        parts = update.message.text.split()

        estate = await get_estate_by_id(int(parts[1]))
        await update.message.reply_text(f'{estate.msg}\n{estate.url}')
    else:
        await update.message.reply_text('Access ERROR')


async def get_estate_group_msg_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN:

        parts = update.message.text.split()
        print(parts)
        # Получение двух значений после команды
        if len(parts) >= 3:
            group_id = parts[1]
            msg_id = int(parts[2])
            print(group_id, '\n', msg_id)
            estate = await get_estate_by_group_id_and_msg_id(group_id, msg_id)
            print(estate)
            if estate:
                print(f'{estate.msg}\n{estate.url}')
                await update.message.reply_text(f'{estate.msg}\n{estate.url}')
        else:
            await update.message.reply_text("error")
    else:
        await update.message.reply_text('Access ERROR')
