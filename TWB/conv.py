import logging
import requests as req

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

SERVICE, WEATHER, CRYPTO, COVID19 = range(4)


def start(update, context):

    reply_keyboard = [['Crypto', 'Weather','COVID-19']]

    update.message.reply_text(
        'Choose a service or send /cancel to stop the bot.',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return SERVICE


def service(update, context):
    user = update.message.from_user
    logger.info("Service %s: %s", user.first_name, update.message.text)

    if update.message.text == "Weather":
        update.message.reply_text('Please send a location.', reply_markup = ReplyKeyboardRemove())
        return WEATHER

    if update.message.text == "Crypto":
        update.message.reply_text('Please send a symbol.', reply_markup=ReplyKeyboardRemove())
        return CRYPTO

    if update.message.text == "COVID-19":
        update.message.reply_text('Please send a country name. (first letter in uppercase)',
                                  reply_markup = ReplyKeyboardRemove())
        return COVID19


def weather(update, context):
    kelvinC = 273.15
    user = update.message.from_user
    try:
        user_location = update.message.location
        logger.info("Location of %s: %f / %f", user.first_name, user_location.latitude,
                    user_location.longitude)
        res = req.request("GET", "http://api.openweathermap.org/data/2.5/weather" +
                          "?lat=" + str(user_location.latitude) +
                          "&lon=" + str(user_location.longitude) +
                          "&appid=fbd3f9a05c6933ecad66013d273847cc").json()
        update.message.reply_text(res["name"] + " weather condition is '" + (res["weather"][0]["description"]).lower() +
                                  "' at the moment. Based on " + res["base"] + " data temperature is " +
                                  str(round(res["main"]["temp"]-kelvinC, 2)) +
                                  ". But it feels like " + str(round(res["main"]["feels_like"]-kelvinC, 2)) + ". " +
                                  "Today's high will be " + str(round(res["main"]["temp_max"]-kelvinC, 2)) +
                                  " and the low will be " + str(round(res["main"]["temp_min"]-kelvinC, 2)) +
                                  ". \n\n\nsource: openweathermap.org\nstart the bot again: /start")
    except:
        update.message.reply_text("An error occurred.\nstart the bot again: /start")
    finally:
        return ConversationHandler.END


def crypto(update, context):
    user = update.message.from_user
    logger.info("Symbol of %s: %s", user.first_name, update.message.text)
    try:
        res = req.request("GET", "https://api.binance.com/api/v3/ticker/price?symbol=" +
                          str(update.message.text).upper()).json()
        update.message.reply_text("The current price of " + res["symbol"] + " is " + res["price"] +
                                  ".\n\n\nsource: Binance.com\nstart the bot again: /start")
    except:
        update.message.reply_text("An error occurred.\nstart the bot again: /start")
    finally:
        return ConversationHandler.END


def covid19(update, context):
    user = update.message.from_user
    logger.info("Country of %s: %s", user.first_name, update.message.text)

    res = req.request("GET", "https://pomber.github.io/covid19/timeseries.json").json()

    try:
        country_name = str(update.message.text)  # .lower()
        # country_name[0] = country_name[0].upper()
        data = res[country_name]
        last = data[len(data)-1]
        update.message.reply_text(("Confirmed: " + str(last["confirmed"]) + "\n" +
                                   "Deaths: " + str(last["deaths"]) + "\n" +
                                   "Recovered: " + str(last["recovered"]) + "\n" +
                                   "Last update: " + last["date"] + "\n" +
                                   "\n\nsource: github.io/covid19\nstart the bot again: /start"))
    except:
        update.message.reply_text("An error occurred.\nstart the bot again: /start")
    finally:
        return ConversationHandler.END


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Thanks for using this bot. Bye!',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("{TOKEN}", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            SERVICE: [MessageHandler(Filters.regex('^(Crypto|Weather|COVID-19)$'), service)],
            WEATHER: [MessageHandler(Filters.location, weather)],
            CRYPTO: [MessageHandler(Filters.text, crypto)],
            COVID19: [MessageHandler(Filters.text, covid19)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

