import asyncio

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, \
    MenuButtonCommands, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.error import TelegramError
from telegram.ext import CallbackQueryHandler, Application, CommandHandler, ContextTypes, MessageHandler, filters, \
    ConversationHandler

from config.data import BOT_TOKEN, LANGUAGES, DEFAULT_LANGUAGE, SLEEP
from db.connect import deactivate_user, get_active_users, get_estates, update_last_msg_id, get_user_by_chat_id, \
    get_estates_in_time_range, update_user_language, get_user_language, insert_user_tg
from parts.admin import admin_commands, get_last_10_eids, get_estate_id, get_estate_group_msg_id

CITY, MIN_VALUE, MAX_VALUE = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    msg = await update.message.reply_text(lang.START_MSG)
    context.user_data['start_msg'] = msg.message_id
    await set_language(update, context)
    return await set_param(update, context)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang_kb = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Ελληνικά", callback_data='lang_el')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    reply_markup = InlineKeyboardMarkup(lang_kb)
    # I'm special stay en version in this place
    msg = await update.message.reply_text(lang.CHOOSE_LANGUAGE, reply_markup=reply_markup)
    context.user_data['language_kb_msg'] = msg.message_id


async def get_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data['language'] = choice.split('_')[1]
    lang = LANGUAGES[context.user_data['language']]
    await update_user_language(update.callback_query.from_user.id, context.user_data['language'])

    try:
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id,
                                         message_id=context.user_data['language_kb_msg'])
    except Exception as e:
        print(2, e)

    try:
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id,
                                         message_id=context.user_data['set_city_selection_msg'])
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id,
                                         message_id=context.user_data['start_msg'])
        msg = await update.callback_query.message.reply_text(lang.START_MSG)
        context.user_data['start_msg'] = msg.message_id
        command_update = Update(update.update_id, message=update.callback_query.message)
        await set_city_selection(command_update, context)
    except Exception as e:
        print(1, e)
        msg = await update.callback_query.message.reply_text(lang.PARAM)
        context.user_data['set_language_msg'] = msg.message_id


async def find_and_set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'language' not in context.user_data:
        try:
            lang_code = await get_user_language(update.message.chat_id)
        except AttributeError:
            lang_code = await get_user_language(update.callback_query.from_user.id)

        context.user_data['language'] = lang_code if lang_code else DEFAULT_LANGUAGE


async def set_param(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await find_and_set_lang(update, context)
    context.user_data['conversation'] = 'param'
    try:
        await context.bot.delete_message(chat_id=update.message.from_user.id,
                                         message_id=context.user_data['set_language_msg'])
    except Exception as e:
        print(3, e)
    return await set_city_selection(update, context)


async def set_city_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = LANGUAGES[context.user_data['language']]
    await deactivate_user(update.message.chat_id)

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(lang.LARNAKA, callback_data="larnaka"),
         InlineKeyboardButton(lang.PAPHOS, callback_data="paphos")],
        [InlineKeyboardButton(lang.NICOSIA, callback_data="nicosia"),
         InlineKeyboardButton(lang.LIMASSOL, callback_data="limassol")],
        [InlineKeyboardButton(lang.CYPRUS, callback_data="cyprus")],
    ])
    if update.callback_query:
        msg = await update.callback_query.message.reply_text(lang.SELECT_CITY, reply_markup=reply_markup)
    else:
        msg = await update.message.reply_text(lang.SELECT_CITY, reply_markup=reply_markup)
    context.user_data['set_city_selection_msg'] = msg.message_id
    return CITY


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['city'] = query.data

    try:
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id,
                                         message_id=context.user_data['language_kb_msg'])

    except Exception as e:
        print(4, e)
    try:
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id,
                                         message_id=context.user_data['start_msg'])

    except Exception as e:
        print(5, e)

    await query.delete_message()
    # await query.edit_message_reply_markup(reply_markup=None)

    return await set_min_price(update, context)


async def invalid_city_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = LANGUAGES[context.user_data['language']]
    await update.message.reply_text(lang.INVALID_INPUT_MSG)
    return await set_city_selection(update, context)


async def set_min_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = LANGUAGES[context.user_data['language']]

    keyboard = [['100', '300', '500', '700', '1000'],
                ['1200', '1400', '1600', '1800', '2000'],
                ['2200', '2500', '3000', '5000', '8000']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    if update.callback_query:
        message = await update.callback_query.message.reply_text(lang.CHOOSE_MIN_PRICE, reply_markup=reply_markup)
    else:
        message = await update.message.reply_text(lang.CHOOSE_MIN_PRICE, reply_markup=reply_markup)

    context.user_data['min_price_message_id'] = message.message_id
    return MIN_VALUE


async def min_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = LANGUAGES[context.user_data['language']]

    text = update.message.text

    # Удаляем сообщение с запросом минимальной цены
    await context.bot.delete_message(chat_id=update.message.chat_id,
                                     message_id=context.user_data['min_price_message_id'])
    await context.bot.delete_message(chat_id=update.message.chat_id,
                                     message_id=update.message.message_id)

    if text.isdigit() and 100 <= int(text) <= 999999:
        context.user_data['min_value'] = text
        keyboard = [['300', '500', '700', '1000', '1200'],
                    ['1400', '1600', '1800', '2000', '2200'],
                    ['2500', '3000', '5000', '8000', '999999']]
        #    [['300', '500', '700', '1000', '1200'], ['1200', '1400', '1600', '1800', '2000']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        message = await update.message.reply_text(lang.CHOOSE_MAX_PRICE, reply_markup=reply_markup)
        context.user_data['max_price_message_id'] = message.message_id
        return MAX_VALUE
    else:
        await update.message.reply_text(lang.INVALID_PRICE_INPUT_MSG)
        return MIN_VALUE


async def max_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = LANGUAGES[context.user_data['language']]

    citys = {'larnaka': lang.LARNAKA, 'paphos': lang.PAPHOS, 'nicosia': lang.NICOSIA,
             'limassol': lang.LIMASSOL, 'cyprus': lang.CYPRUS}
    max_value = update.message.text

    await context.bot.delete_message(chat_id=update.message.chat_id,
                                     message_id=context.user_data['max_price_message_id'])
    await context.bot.delete_message(chat_id=update.message.chat_id,
                                     message_id=update.message.message_id)

    if max_value.isdigit() and 100 <= int(max_value) <= 999999:
        if int(context.user_data['min_value']) > int(max_value):

            context.user_data['max_value'], context.user_data['min_value'] = context.user_data['min_value'], max_value
        else:
            context.user_data['max_value'] = max_value

        await insert_user_tg(update.message.chat_id,
                             context.user_data['city'],
                             int(context.user_data['min_value']),
                             int(context.user_data['max_value']),
                             context.user_data['language']
                             )

        message = await update.message.reply_text(
            f"{lang.CONFIRMATION_MSG} \n\n"
            f"{lang.CITY}: {citys[context.user_data['city']]} \n"
            f"{lang.MIN_PRICE} {context.user_data['min_value']}€ "
            f"{lang.MAX_PRICE} {context.user_data['max_value']}€\n{lang.STOP_UPDATE}{lang.PARAM}",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data['set_all_params'] = message.message_id

        await history_bt(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text(lang.INVALID_PRICE_INPUT_MSG)
        return MAX_VALUE


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    if await deactivate_user(update.message.chat_id):
        await update.message.reply_text(lang.UPDATE_STOPPED)
    else:
        await update.message.reply_text(lang.MSG_ERROR)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]
    await update.message.reply_text(lang.INFO_BOT)


async def history_bt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    history_kb = [
        [InlineKeyboardButton(lang.GET_DAY_HISTORY_BT, callback_data='get_day_history_kb')],
        [InlineKeyboardButton(lang.DEL_HISTORY_BT, callback_data='del_history_kb')],
    ]
    reply_markup = InlineKeyboardMarkup(history_kb)
    # I'm special stay en version in this place
    msg = await update.message.reply_text(lang.TXT_BEFORE_HISTORY_BT, reply_markup=reply_markup)
    context.user_data['history_bt_msg'] = msg.message_id


async def get_day_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    await del_history_kb(update, context)

    user = await get_user_by_chat_id(update.message.from_user.id)
    if user:
        msg = ''
        match context.user_data['language']:
            case 'ru':
                msg = 'msg_ru'
            case 'en':
                msg = 'msg_en'
            case 'el':
                msg = 'msg_el'

        estates = await get_estates_in_time_range(city=user.city, min_price=user.min_price, max_price=user.max_price,
                                                  range_time=24, field_msg=msg)
        for estate in estates[0:5]:  # -----------!!!!!!!!!!!!!------------!!!!!!!!!!!!-------!!!!!!!!! TEST
            msg_to_sent = f'{estate[0]}\n{estate[1]}'
            if len(msg_to_sent) <= 4095:
                await update.message.reply_text(msg_to_sent)
            else:
                continue
    else:
        await update.message.reply_text(lang.ERROR_SET_DATA)


async def del_history_kb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id,
                                         message_id=context.user_data['history_bt_msg'])
        await context.bot.delete_message(chat_id=update.callback_query.from_user.id,
                                         message_id=context.user_data['set_all_params'])

    except Exception as e:
        print(e)


async def get_day_history_kb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    user = await get_user_by_chat_id(update.callback_query.from_user.id)
    if user:
        msg = ''
        match context.user_data['language']:
            case 'ru':
                msg = 'msg_ru'
            case 'en':
                msg = 'msg_en'
            case 'el':
                msg = 'msg_el'

        estates = await get_estates_in_time_range(city=user.city, min_price=user.min_price, max_price=user.max_price,
                                                  range_time=24, field_msg=msg)
        for estate in estates:
            msg_to_sent = f'{estate[0]}\n{estate[1]}'
            if len(msg_to_sent) <= 4095:
                await update.callback_query.message.reply_text(msg_to_sent)
            else:
                continue
    else:
        await update.callback_query.message.reply_text(lang.ERROR_SET_DATA)


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
                lang = LANGUAGES[user.set_language]
                msg = ''
                match user.set_language:
                    case 'ru':
                        msg = estate.msg_ru
                    case 'en':
                        msg = estate.msg_en
                    case 'el':
                        msg = estate.msg_el
                try:
                    msg_to_sent = f'{msg}{lang.LINK_TO_ADD}{estate.url}'
                    if len(msg_to_sent) <= 4095:
                        await application.bot.send_message(chat_id=user.chat_id, text=msg_to_sent)

                except TelegramError as e:
                    await deactivate_user(user.chat_id)
                    print(f"------------------------{e}----------------------")
            if flag:
                try:
                    lang = LANGUAGES[user.set_language]
                    await application.bot.send_message(chat_id=user.chat_id,
                                                       text=f'{lang.STOP_UPDATE}{lang.PARAM}')

                except TelegramError as e:
                    await deactivate_user(user.chat_id)
                    print(f"------------------------{e}----------------------")
            await update_last_msg_id(user.chat_id, last_msg_id)

        await asyncio.sleep(SLEEP)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    if await deactivate_user(update.message.chat_id):
        await update.message.reply_text(lang.UPDATE_STOPPED)
    else:
        await update.message.reply_text(lang.MSG_ERROR)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await find_and_set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]
    await update.message.reply_text(lang.INFO_BOT)


async def set_bot_commands(application: Application) -> None:
    lang = LANGUAGES[DEFAULT_LANGUAGE]

    commands = [
        BotCommand("new_parameters", lang.NEW_PARAM_COMMAND),
        BotCommand("language", lang.CHANGE_LANGUAGE_COMMAND),
        BotCommand("get_day_history", lang.GET_HISTORY_COMMAND),
        BotCommand("my_parameters", lang.MY_PARAM_COMMAND),
        BotCommand("stop", lang.STOP_UPDATE_COMMAND),
        BotCommand("info", lang.INFO_BOT_COMMAND)
    ]

    await application.bot.set_my_commands(commands)
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


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
                    msg_to_sent = f'{msg}{lang.LINK_TO_ADD}{estate.url}'
                    if len(msg_to_sent) <= 4095:
                        await application.bot.send_message(chat_id=user.chat_id, text=msg_to_sent)

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

        await asyncio.sleep(60)


async def on_startup(application: Application) -> None:
    await set_bot_commands(application)
    asyncio.create_task(update_loop(application))


def main() -> None:
    """Start the bot."""

    application = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('new_parameters', set_param)],
        states={
            CITY: [CallbackQueryHandler(set_city), MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_city_input)],
            MIN_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, min_price)],
            MAX_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_price)]
        },
        fallbacks=[CommandHandler('start', start),
                   CommandHandler('new_parameters', set_param),
                   CommandHandler('language', set_language)],
        per_message=False)

    application.add_handler(CommandHandler('info', info))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('language', set_language))
    application.add_handler(CommandHandler('get_day_history', get_day_history))

    application.add_handler(CallbackQueryHandler(get_language, pattern='^lang_(en|el|ru)$'))
    application.add_handler(CallbackQueryHandler(get_day_history_kb, pattern='^get_day_history_kb$'))
    application.add_handler(CallbackQueryHandler(del_history_kb, pattern='^del_history_kb$'))

    # Admin command
    application.add_handler(CommandHandler('admin', admin_commands))
    application.add_handler(CommandHandler('eid', get_last_10_eids))
    application.add_handler(CommandHandler('msgid', get_estate_id))
    application.add_handler(CommandHandler('groupid', get_estate_group_msg_id))

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
