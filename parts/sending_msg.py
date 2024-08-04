import asyncio
from datetime import datetime, timedelta

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError, Forbidden
from telegram.ext import Application

from config.data import LANGUAGES, SLEEP, TIME_SEND_MSG, TIME_SEND_VIP_MSG
from db.connect import get_estates, deactivate_user, update_last_msg_id, get_active_usual_users, get_active_vip_users, \
    rewrite_update_msgs_time
from db.create import User


async def update_loop(application: Application) -> None:
    count = 0
    while True:
        count += 1
        vip_users = await get_active_vip_users()
        users = await get_active_usual_users()
        now = datetime.now()

        for user in vip_users:
            if (now - user.last_update_msgs_time) >= timedelta(seconds=TIME_SEND_VIP_MSG):
                await send_msg_to_user(user, application)
                if not await rewrite_update_msgs_time(user.chat_id, now):
                    print(f"Error = не удачная перезапись времени отправки последнего сообщения @{user.username}")

        for user in users:
            if (now - user.last_update_msgs_time) >= timedelta(seconds=TIME_SEND_MSG):
                await send_msg_to_user(user, application)
                if not await rewrite_update_msgs_time(user.chat_id, now):
                    print(f"Error = не удачная перезапись времени отправки последнего сообщения @{user.username}")

        print(f'================== --- {count} --- ==================')
        print(f'======--- {datetime.now()} --- ======')
        await asyncio.sleep(SLEEP)


async def send_msg_to_user(user: User, application: Application) -> None:
    flag = False
    last_msg_id = user.last_msg_id
    estates = await get_estates(user.last_msg_id, user.city, user.min_price, user.max_price)
    if estates:
        print(f'for user = {user.chat_id}')
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
                link_kb = InlineKeyboardMarkup([[InlineKeyboardButton(lang.OPEN_LINK, url=estate.url)]])

                if len(msg_to_sent) <= 4095:

                    await application.bot.send_message(chat_id=user.chat_id,
                                                       text=msg_to_sent,
                                                       reply_markup=link_kb)
                elif len(msg_to_sent) <= 8185:
                    await application.bot.send_message(chat_id=user.chat_id,
                                                       text=msg_to_sent[:4090])
                    await application.bot.send_message(chat_id=user.chat_id,
                                                       text=msg_to_sent[4090:],
                                                       reply_markup=link_kb)

            except Forbidden as e:
                await deactivate_user(user.chat_id)
                print(f"------------------------{e}----------------------")

            except TelegramError as e:
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

