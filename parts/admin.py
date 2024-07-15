import re

from telegram import Update, InputMediaVideo, InputMediaPhoto
from telegram.error import TelegramError, Forbidden
from telegram.ext import ContextTypes

from config.data import ADMIN
from db.connect import get_last_10_estate_ids, get_estate_by_id, get_estate_by_group_id_and_msg_id, get_all_users, \
    deactivate_user


async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN:
        menu_text = """
        Меню администратора:
            /get_user_list - all users
            /ad - send ad to all users Ex : + ' advt text and/or {just_one_photo_or_video}'
            /eid - get last 10 Estate.id Ex: + ''\n
            /msgid - get msg with Estate.id Ex: + ' 357'\n
            /groupid - get msg with group_id and msg_id Ex: + ' dom_com_cy 105200'\n
            /u_list - get user list\n
            """
        await update.message.reply_text(menu_text)
    else:
        await update.message.reply_text('Access ERROR')


async def get_user_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id == ADMIN:
        users, amount = await get_all_users()
        count = 0
        for user in users:
            count += 1
            await update.message.reply_text(f'{count}. {user.chat_id} {user.status}')
    else:
        await update.message.reply_text('Access ERROR')


async def ad_check_cmd_in_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    print('post_ad_post_check_command')
    if user_id == ADMIN:
        regx = r'^/ad'

        # Проверка наличия фотографий и видео в сообщении
        if update.message.photo or update.message.video:
            caption = update.message.caption
            if caption and re.search(regx, caption):
                await post_ad_post(update, context)


# Ограничения: отправка одного файла фото или видео с текстом
# На будующее: добавить кнопку если будет юрл
async def post_ad_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    print('post_ad_post start')
    if user_id == ADMIN:
        media = []
        caption = update.message.text or ''

        # Проверка наличия фотографий в сообщении
        if update.message.photo:
            caption = update.message.caption[4:]
            photo = max(update.message.photo, key=lambda p: p.file_size)
            media.append(InputMediaPhoto(media=photo.file_id, caption=caption))
            print(photo)

        # Проверка наличия видео в сообщении
        if update.message.video:
            caption = update.message.caption
            video = max(update.message.video, key=lambda p: p.file_size)
            media.append(
                InputMediaVideo(media=video.file_id, caption=caption))
            print(video)

        users = await get_all_users()
        for user in users:
            try:
                if media:
                    print('if media true')
                    await context.bot.send_media_group(chat_id=user.chat_id, media=media)
                else:
                    if caption:
                        print('if media =   fals and captio = true')
                        await context.bot.send_message(chat_id=user.chat_id, text=caption)

            except Forbidden as e:
                await deactivate_user(user.chat_id)
                print(f"------------------------{e}----------------------")

            except TelegramError as e:
                await deactivate_user(user.chat_id)
                print(f"------------------------{e}----------------------")
                continue
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
