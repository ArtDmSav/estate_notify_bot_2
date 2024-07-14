import asyncio

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove, MenuButtonCommands
from telegram.error import TelegramError
from telegram.ext import CallbackQueryHandler, Application, CommandHandler, ContextTypes, MessageHandler, filters, \
    ConversationHandler

from config.data import BOT_TOKEN, LANGUAGES, DEFAULT_LANGUAGE, ADMIN
from db.connect import insert_user_tg, deactivate_user, get_active_users, get_estates, update_last_msg_id, \
    get_user_language, get_last_10_estate_ids, get_estate_by_id, get_estate_by_group_id_and_msg_id, get_user_by_chat_id, \
    get_estates_in_time_range, update_user_language

CITY, MIN_VALUE, MAX_VALUE = range(3)


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'language' not in context.user_data:
        try:
            lang_code = await get_user_language(update.message.chat_id)
        except AttributeError:
            lang_code = await get_user_language(update.callback_query.from_user.id)

        context.user_data['language'] = lang_code if lang_code else DEFAULT_LANGUAGE


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await set_lang(update, context)

    lang = LANGUAGES[context.user_data['language']]
    await update.message.reply_text(lang.LANGUAGE_SET)
    return await set_param(update, context)


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang_kb = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Ελληνικά", callback_data='lang_el')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(lang_kb)
    # I'm special stay en version in this place
    await update.message.reply_text("Please choose your language:", reply_markup=reply_markup)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data['language'] = choice.split('_')[1]
    await update_user_language(update.callback_query.from_user.id, context.user_data['language'])
    lang = LANGUAGES[context.user_data['language']]
    await update.callback_query.edit_message_text(lang.CHANGE_LANGUAGE)


async def set_param(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await set_lang(update, context)
    context.user_data['conversation'] = 'param'
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
        await update.callback_query.message.reply_text(lang.SELECT_CITY, reply_markup=reply_markup)
    else:
        await update.message.reply_text(lang.SELECT_CITY, reply_markup=reply_markup)
    return CITY


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['city'] = query.data

    await query.delete_message()
    # await query.edit_message_reply_markup(reply_markup=None)

    return await set_min_price(update, context)


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

        await update.message.reply_text(
            f"{lang.CONFIRMATION_MSG} \n\n"
            f"{lang.CITY}: {citys[context.user_data['city']]} \n"
            f"{lang.MIN_PRICE} {context.user_data['min_value']}€ "
            f"{lang.MAX_PRICE} {context.user_data['max_value']}€\n{lang.STOP_UPDATE}{lang.PARAM}",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(lang.INVALID_PRICE_INPUT_MSG)
        return MAX_VALUE


async def invalid_city_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = LANGUAGES[context.user_data['language']]
    await update.message.reply_text(lang.INVALID_INPUT_MSG)
    return await set_city_selection(update, context)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

    if await deactivate_user(update.message.chat_id):
        await update.message.reply_text(lang.UPDATE_STOPPED)
    else:
        await update.message.reply_text(lang.MSG_ERROR)


async def get_day_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]

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
        for estate in estates:
            await update.message.reply_text(f'{estate[0]}\n{estate[1]}')
    else:
        await update.message.reply_text(lang.ERROR_SET_DATA)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_lang(update, context)
    lang = LANGUAGES[context.user_data['language']]
    await update.message.reply_text(lang.INFO_BOT)


async def set_bot_commands(application: Application, language_code: str) -> None:
    lang = LANGUAGES[DEFAULT_LANGUAGE]

    commands = [
        BotCommand("start", lang.BOT_START),
        BotCommand("new_parameters", lang.NEW_PARAM),
        BotCommand("language", lang.CHANGE_LANGUAGE_COMMAND),
        BotCommand("get_day_history", lang.GET_DAY_HISTORY),
        BotCommand("info", lang.INFO_BOT_COMMAND)
    ]

    await application.bot.set_my_commands(commands)
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN:
        menu_text = """
            Меню администратора:
            /eid - get last 10 Estate.id Ex: + ''
            /msgid - get msg with Estate.id Ex: + ' 357'
            /groupid - get msg with group_id and msg_id Ex: + ' dom_com_cy 105200'
            /u_list - get user list
            
    application.add_handler(CommandHandler('', get_last_10_eids))
    application.add_handler(CommandHandler('', get_estate_id))
    application.add_handler(CommandHandler('groupid', get_estate_group_msg_id))
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
                    await application.bot.send_message(chat_id=user.chat_id,
                                                       text=f'{msg}{lang.LINK_TO_ADD}{estate.url}')

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
    # Set default language
    await set_bot_commands(application, DEFAULT_LANGUAGE)
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
                   CommandHandler('language', language)],
        per_message=False)

    application.add_handler(CommandHandler('info', info))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('language', language))
    application.add_handler(CommandHandler('get_day_history', get_day_history))

    application.add_handler(CallbackQueryHandler(set_language, pattern='^lang_(en|el|ru)$'))

    # Admin command
    application.add_handler(CommandHandler('admin', admin_commands))
    application.add_handler(CommandHandler('eid', get_last_10_eids))
    application.add_handler(CommandHandler('msgid', get_estate_id))
    application.add_handler(CommandHandler('groupid', get_estate_group_msg_id))

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
