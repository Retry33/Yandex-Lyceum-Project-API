from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackContext
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update

from googletrans import Translator
import math
import datetime
from datetime import timezone, timedelta
import requests

from data import db_session
from data.users import User

from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
OpenWeather_TOKEN = os.getenv('OPENWEATHER_TOKEN')
Geocoder_TOKEN = os.getenv('GEOCODER_TOKEN')
CURRENCY_TOKEN = os.getenv("CURRENCY_TOKEN")
ENTER_CURRENCY_PAIR = 0

code_to_smile = {
    "Clear": "Ясно \U00002600",
    "Clouds": "Облачно \U00002601",
    "Rain": "Дождь \U00002614",
    "Drizzle": "Дождь \U00002614",
    "Thunderstorm": "Гроза \U000026A1",
    "Snow": "Снег \U0001F328",
    "Mist": "Туман \U0001F32B"
}
translator = Translator()
LANGUAGES = {
    'русского': 'ru', 'русский': 'ru',
    'английского': 'en', 'английский': 'en',
    'испанский': 'es', 'испанского': 'es',
    'канадский': 'kn', 'канадского': 'kn',
    'португальский': 'pt', 'португальского': 'pt',
    'арабский': 'ar', 'арабского': 'ar',
    'немецкий': 'de', 'немецкого': 'de',
    'французский': 'fr', 'французского': 'fr',
    'хинди': 'hi',
    'греческий': 'el', 'греческого': 'el'
}


def get_keyboard_for_menu():
    wether_button = KeyboardButton('☀Моя погода☀', request_location=True)
    reply_keyboard = KeyboardButton('/notification')
    my_keboard = ReplyKeyboardMarkup([['🙏Помощь🙏'], [wether_button, '🌦Погода🌦'], ['🈳Переводчик🈳'], [reply_keyboard]],
                                     resize_keyboard=True)
    return my_keboard


def get_keyboard_for_translator():
    my_keboard = ReplyKeyboardMarkup(
        [['русский', 'английский'], ['испанский', 'канадский'], ['португальский', 'арабский'],
         ['немецкий', 'французский'], ['хинди', 'греческого'], ['/stop']], resize_keyboard=True)
    return my_keboard


def get_keyboard_for_text():
    my_keboard = ReplyKeyboardMarkup([['/stop']], resize_keyboard=True)
    return my_keboard


def get_keyboard_stop():
    reply_keyboard = KeyboardButton('/stop')
    my_keboard = ReplyKeyboardMarkup([[reply_keyboard]], resize_keyboard=True,
                                     one_time_keyboard=True)
    return my_keboard


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"👋👋👋Привет {user.mention_html()}! Я бот-помошник для путешествий...\n\n\n❓Чтобы подробнее узнать о моих "
        f"функциях используйте команду /help или нажмите на кнопку «Помошь»❓.",
        reply_markup=get_keyboard_for_menu())


async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_html(
        "❗В данном сообщении вы можете узнать о всём функционале бота❗\n\n\n"
        "🔸<u><b>Карманный переводчик</b></u>\n"
        "Чтобы получить перевод любого слова или фразы отправьте мне сообщение со следующим "
        "содержанием:\n<b>Переведи с</b> <i>язык переводимой фразы</i> <b>на</b> <i>язык "
        "результата</i> ...\nПример: Переведи с русского на английский Привет мир!\n\n\n"
        "🔸<u><b>Синоптик</b></u>\n"
        "Если вы хотите узнать текущую погоду в городе вашего прибывания нажмите на кнопку "
        "«Моя погода», при этом в чат будет отправлена информация о вашей геолокации.\n\n"
        "Если вас интересует погода в конкретном городе, то отправьте мне сообщение со "
        "следующим содержанием:\n<b>Погода в городе</b> <i>название города</i>\nПример: "
        "Погода в городе Москва", reply_markup=get_keyboard_for_menu())


def wether(city):
    global code_to_smile

    response = requests.get(
        f"http://api.openweathermap.org/data/2.5/weather?q={city}&lang=ru&units=metric&appid={OpenWeather_TOKEN}")
    data = response.json()
    city = data["name"]
    cur_temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]

    # продолжительность дня
    length_of_the_day = datetime.datetime.fromtimestamp(
        data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(data["sys"]["sunrise"])

    weather_description = data["weather"][0]["main"]

    time_zone = data["timezone"]

    tz = timezone(timedelta(seconds=time_zone))

    if weather_description in code_to_smile:
        wd = code_to_smile[weather_description]
    else:
        # если эмодзи для погоды нет, выводим другое сообщение
        wd = "Посмотри в окно, я не понимаю, что там за погода..."
    return f"⌚{datetime.datetime.now(tz).strftime('%d-%m-%Y %H:%M')}\n\n" \
           f"🟠<u><b>Погода в городе {city}</b></u>🟠\n\n" \
           f"🌡Температура: {cur_temp}°C {wd}\n" \
           f"💧Влажность: {humidity}%\n" \
           f"🌍Давление: {math.ceil(pressure / 1.333)} мм.рт.ст\n" \
           f"💨Ветер: {wind} м/с \n" \
           f"🌘Продолжительность дня: {length_of_the_day}"


async def my_wether(update, context):
    global Geocoder_TOKEN
    Location = str(update.message.location).split('Location(latitude=')
    Location = Location[1].split(', longitude=')
    latitude, longitude = Location[0], Location[1]

    headers = {"Accept-Language": "ru"}
    address = requests.get(
        f'https://eu1.locationiq.com/v1/reverse.php?key={Geocoder_TOKEN}&lat={latitude}&lon={longitude[:-1]}'
        f'&format=json',
        headers=headers).json()
    await update.message.reply_html(wether(address["address"].get("city")), reply_markup=get_keyboard_for_menu())


# Начало диалога с переводчиком
async def translation(update, context):
    await update.message.reply_text("Введите текст для перевода.", reply_markup=get_keyboard_for_text())
    return 1


async def start_language(update, context):
    context.user_data['text'] = update.message.text
    await update.message.reply_text(
        f"Введите начальный язык (с какого хотите перевести).", reply_markup=get_keyboard_for_translator())
    return 2


async def end_language(update, context):
    context.user_data['src'] = update.message.text
    await update.message.reply_text(
        f"Введите конечный язык (на какой хотите перевести).", reply_markup=get_keyboard_for_translator())
    return 3


async def end_translation(update, context):
    try:
        src = LANGUAGES[context.user_data['src']]
        dest = LANGUAGES[update.message.text]
        text = context.user_data['text']

        await update.message.reply_text(translator.translate(text, src=src, dest=dest).text,
                                        reply_markup=get_keyboard_for_menu())
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as error:
        print(error)
        await update.message.reply_text(
            "Соединение с сервером потеряно. Попробуйте ввести корректные названия языков или подождите немного",
            reply_markup=get_keyboard_for_menu())
        context.user_data.clear()
        return ConversationHandler.END


# Конец диалога с переводчиком
# Начало диалога с синоптиком
async def city_wether(update, context):
    await update.message.reply_text("В каком городе желаете узнать погоду?.", reply_markup=get_keyboard_for_text())
    return 1


async def end_wether(update, context):
    try:
        city = update.message.text
        await update.message.reply_html(wether(city), reply_markup=get_keyboard_for_menu())
        return ConversationHandler.END

    except Exception as error:
        print(error)
        await update.message.reply_text(
            "Соединение с сервером потеряно. Попробуйте ввести корректное название города или подождите немного.",
            reply_markup=get_keyboard_for_menu())
        return ConversationHandler.END


# Конец диалога с синоптиком
async def stop(update, context):
    await update.message.reply_text("Галя, у нас отмена!", reply_markup=get_keyboard_for_menu())
    return ConversationHandler.END


async def echo(update, context):
    global translator, LANGUAGES
    if 'Переведи' in update.message.text:
        try:
            src = LANGUAGES[update.message.text.split()[2]]
            dest = LANGUAGES[update.message.text.split()[4]]
            text = ' '.join(update.message.text.split()[5:])

            await update.message.reply_text(translator.translate(text, src=src, dest=dest).text,
                                            reply_markup=get_keyboard_for_menu())
        except Exception as error:
            print(error)
            await update.message.reply_text(
                "Соединение с сервером потеряно. Попробуйте ввести корректные названия языков или подождите немного",
                reply_markup=get_keyboard_for_menu())

    elif 'Погода в городе' in update.message.text:
        try:
            city = update.message.text.split('Погода в городе ')[-1]
            await update.message.reply_html(wether(city), reply_markup=get_keyboard_for_menu())

        except Exception as error:
            print(error)
            await update.message.reply_text(
                "Соединение с сервером потеряно. Попробуйте ввести корректное название города или подождите немного.",
                reply_markup=get_keyboard_for_menu())


# Команда обработки обменного курса
async def exchange_rate_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Пожалуйста, введите валютную пару в формате 'USD/RUB':")
    return ENTER_CURRENCY_PAIR


# Обработка ввода пользователем валютной пары
async def handle_currency_pair(update: Update, context: CallbackContext):
    try:
        base_currency, target_currency = update.message.text.split('/')
        response = requests.get(f'https://v6.exchangerate-api.com/v6/{CURRENCY_TOKEN}/latest/{base_currency}')
        data = response.json()
        if data['result'] == 'success':
            rate = data['conversion_rates'].get(target_currency.upper())
            if rate:
                await update.message.reply_text(
                    f"Текущий курс {base_currency}/{target_currency}: 1 {base_currency} = {rate} {target_currency}")
                return ConversationHandler.END
            else:
                await update.message.reply_text(f"Извините, курс для пары {base_currency}/{target_currency} не найден.")
        else:
            await update.message.reply_text("Извините, курсы валют не доступны.")
    except Exception as e:
        await update.message.reply_text("Пожалуйста, укажите валютную пару в правильном формате.")
    return ENTER_CURRENCY_PAIR


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def task(context):
    await context.bot.send_message(context.job.chat_id, text=f'Напомниаю {TEXT}!')


async def notification(update, context):
    await update.message.reply_text("О чем вам напомнить?")
    return 1


async def first_response(update, context):
    context.user_data['time'] = update.message.text
    await update.message.reply_text(
        f'Через сколько секунд вам напомнить "{context.user_data["time"]}"?')
    # Следующее текстовое сообщение будет обработано
    # обработчиком states[2]
    return 2


async def second_response(update, context):
    global TIMER, TEXT
    time = update.message.text
    TIMER = int(time)
    TEXT = context.user_data['time']
    chat_id = update.effective_message.chat_id
    context.job_queue.run_once(task, TIMER, chat_id=chat_id, name=str(chat_id), data=TIMER)
    text = f'Вернусь через {TIMER} c.!'
    await update.effective_message.reply_text(text, reply_markup=get_keyboard_stop())
    return ConversationHandler.END


async def stop_dialog(update, context):
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Напоминание отменено! Всего доброго!' if job_removed else 'У вас нет активных напоминаний'
    context.user_data.clear()
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def close_keyboard(update, context):
    await update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove()
    )


def main():
    # Запуск бота.
    application = Application.builder().token(BOT_TOKEN).build()

    db_session.global_init("db/fast_translator.db")

    # Регистрация комманд.
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("close", close_keyboard))
    application.add_handler(CommandHandler('stop_dialog', stop_dialog))

    translation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('🈳Переводчик🈳'), translation)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_language)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_language)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_translation)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(translation_handler)

    wether_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('🌦Погода🌦'), city_wether)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_wether)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('exchange', exchange_rate_command)],
        states={
            ENTER_CURRENCY_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_currency_pair)],
        },
        fallbacks=[],
    )

    conver_handler = ConversationHandler(
        entry_points=[CommandHandler('notification', notification)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)]
        },
        fallbacks=[CommandHandler('stop_dialog', stop_dialog)]
    )

    application.add_handler(conver_handler)
    application.add_handler(wether_handler)
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex('🙏Помощь🙏'), help_command))
    application.add_handler(MessageHandler(filters.LOCATION, my_wether))
    application.add_handler(MessageHandler(filters.TEXT, echo))

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
