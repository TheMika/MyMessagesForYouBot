#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import json
import logging
import os
from datetime import datetime

import telegram
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    PicklePersistence,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

with open("keys.txt", "r") as f:
    secrets = json.loads(f.read())
bot = telegram.Bot(token=secrets["token"])

logger = logging.getLogger(__name__)

START, TYPING_MESSAGE = range(2)

NEW_MESSAGE_DESC = 'نوشته جدید'
DEL_MESSAGE_DESC = 'حذف نوشته'
GET_MESSAGE_DESC = 'دریافت نوشته'
MY_MESSAGES_DESC = 'نوشته‌های من'
reply_keyboard = [
    [NEW_MESSAGE_DESC]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def get_message(x, opt=False):
    if opt:
        return \
            "فرستنده:{} \n گیرنده: {}\nتاریخ ایجاد: {}\n{}".format(x[0], x[1], x[3].strftime("%Y-%m-%d %H:%M:%S"), x[2])
    else:
        return "تاریخ ایجاد: {}\n{}".format(x[3].strftime("%Y-%m-%d %H:%M:%S"), x[2])


def messages_to_str(bot_data):
    facts = list()

    for key, value in bot_data.items():
        facts.append("\n\n".join([get_message(x, True) for x in value]))

    return "\n\n\n".join(facts)


def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    if 'users' not in context.bot_data:
        context.bot_data = []
    if update.message.from_user.username.lower() not in context.bot_data['users']:
        bot.sendMessage(secrets["admin"], "new user " + update.message.from_user.username.lower())
        context.bot_data['users'].append(update.message.from_user.username.lower())
    if update.message.text.split()[0] != '/start':
        update.message.reply_text("ببخشید متوجه نشدم!", reply_markup=markup)
        return START
    elif len(update.message.text.split()) == 1:
        update.message.reply_text("سلام، چه کاری میتونم برات انجام بدم؟", reply_markup=markup)
        return START
    inviter_user = update.message.text.split()[1].lower()
    to_user = update.message.from_user.username.lower()
    reply_text = ""
    if (inviter_user, to_user) in context.bot_data:
        reply_text += (
            "نوشته‌های ارسال شده از این مخاطب:\n {}".format("\n\n".join(
                [get_message(x) for x in context.bot_data[(inviter_user, to_user)]]
            ))
        )
    else:
        reply_text += (
            "این شخص به شما نوشته‌ای ارسال نکرده است"
        )
    bot.sendMessage(secrets["admin"], "new update")
    update.message.reply_text(reply_text, reply_markup=markup)
    return START


def create_message_start(update, context):
    update.message.reply_text("ابتدا در خط اول آیدی مخاطب و در خط‌های بعدی نوشته خود را بنویسید")
    return TYPING_MESSAGE


def create_message(update, context):
    if len(update.message.text.split('\n')) < 2:
        update.message.reply_text("ببخشید متوجه نشدم!", reply_markup=markup)
        return START
    to_user = update.message.text.split('\n')[0]
    text = update.message.text[len(to_user):]
    from_user = update.message.from_user.username.lower()
    if len(to_user) < 5 or to_user[0] != '@':
        update.message.reply_text("آیدی مخاطب صحیح نیست", reply_markup=markup)
        return START
    else:
        to_user = to_user[1:]
    if (from_user, to_user) not in context.bot_data:
        context.bot_data[(from_user, to_user)] = []
    context.bot_data[(from_user, to_user)].append([from_user, to_user, text, datetime.now()])
    update.message.reply_text(
        'نوشته شما ذخیره شد'
    )

    return START


def show_data(update, context):
    update.message.reply_text(
        format(messages_to_str(context.bot_data))
    )


def main():
    proxy = 'http://127.0.0.1:38673/'
    os.environ['http_proxy'] = proxy
    os.environ['HTTP_PROXY'] = proxy
    os.environ['https_proxy'] = proxy
    os.environ['HTTPS_PROXY'] = proxy

    # Create the Updater and pass it your bot's token.
    pp = PicklePersistence(filename='messages_data')
    updater = Updater(secrets["token"], persistence=pp, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [
                CommandHandler('start', start),
                MessageHandler(Filters.regex('^' + NEW_MESSAGE_DESC + '$'), create_message_start),
            ],
            TYPING_MESSAGE: [
                MessageHandler(
                    Filters.text, create_message
                )
            ],
        },
        fallbacks=[CommandHandler('cancel', start)],
        name="my_conversation",
        persistent=True,
    )

    dp.add_handler(conv_handler)
    show_data_handler = CommandHandler(secrets["show_data"], show_data)
    dp.add_handler(show_data_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
