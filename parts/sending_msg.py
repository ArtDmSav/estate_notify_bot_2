import asyncio

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from telegram.ext import Application

from config.data import LANGUAGES, SLEEP
from db.connect import get_active_users, get_estates, deactivate_user, update_last_msg_id


async def update_loop(application: Application) -> None:
    count = 0
    while True:
        count += 1
        print(f'================== --- {count} --- ==================')
        users = await get_active_users()
        for user in users:
            flag = False
            print(f'user = {user.chat_id}')
            last_msg_id = user.last_msg_id
            estates = await get_estates(user.last_msg_id, user.city, user.min_price, user.max_price)
            for estate in estates:
                flag = True
                last_msg_id = estate.id
                print('estate_id = ', estate.id)
                lang = LANGUAGES[user.language]
                msg = ''
                match user.language:
                    case 'ru':
                        msg = estate.msg_ru
                    case 'en':
                        msg = estate.msg_en
                    case 'el':
                        msg = estate.msg_el
                try:
                    msg_to_sent = f'{msg}\n{estate.url}'
                    if len(msg_to_sent) <= 4095:
                        # await application.bot.send_message(chat_id=user.chat_id, text=msg_to_sent)

                        link_kb = InlineKeyboardMarkup([[InlineKeyboardButton(lang.OPEN_LINK, url=estate.url)]])
                        await application.bot.send_message(chat_id=user.chat_id, text=msg_to_sent, reply_markup=link_kb)

                except TelegramError as e:
                    await deactivate_user(user.chat_id)
                    print(f"------------------------{e}----------------------")
            if flag:
                try:
                    lang = LANGUAGES[user.language]
                    await application.bot.send_message(chat_id=user.chat_id,
                                                       text=f'{lang.STOP_UPDATE}{lang.PARAM}')

                except TelegramError as e:
                    await deactivate_user(user.chat_id)
                    print(f"------------------------{e}----------------------")
            await update_last_msg_id(user.chat_id, last_msg_id)

        await asyncio.sleep(SLEEP)

#
# async def update_loop(application: Application) -> None:
#     count = 0
#     while True:
#         count += 1
#         print(f'================== --- {count} --- ==================')
#         users = await get_active_users()
#         for user in users:
#             flag = False
#             print(f'user = {user.chat_id}')
#             last_msg_id = user.last_msg_id
#             estates = await get_estates(user.last_msg_id, user.city, user.min_price, user.max_price)
#             for estate in estates:
#                 flag = True
#                 last_msg_id = estate.id
#                 print('estate_id = ', estate.id)
#                 lang = LANGUAGES[user.language]
#                 msg = ''
#                 match user.language:
#                     case 'ru':
#                         msg = estate.msg_ru
#                     case 'en':
#                         msg = estate.msg_en
#                     case 'el':
#                         msg = estate.msg_el
#                 try:
#                     msg_to_sent = f'{msg}{lang.LINK_TO_ADD}{estate.url}'
#                     if len(msg_to_sent) <= 4095:
#                         await application.bot.send_message(chat_id=user.chat_id, text=msg_to_sent)
#
#                 except TelegramError as e:
#                     await deactivate_user(user.chat_id)
#                     print(f"------------------------{e}----------------------")
#             if flag:
#                 try:
#                     lang = LANGUAGES[user.set_language]
#                     await application.bot.send_message(chat_id=user.chat_id,
#                                                        text=f'{lang.STOP_UPDATE}{lang.PARAM}')
#
#                 except TelegramError as e:
#                     await deactivate_user(user.chat_id)
#                     print(f"------------------------{e}----------------------")
#             await update_last_msg_id(user.chat_id, last_msg_id)
#
#         await asyncio.sleep(SLEEP)
