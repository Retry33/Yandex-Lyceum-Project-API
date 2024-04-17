from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton

from googletrans import Translator
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import math
import datetime
from datetime import timezone, timedelta
import requests

from dotenv import load_dotenv
import os

SqlAlchemyBase = orm.declarative_base()

__factory = None

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
OpenWeather_TOKEN = os.getenv('OPENWEATHER_TOKEN')
Geocoder_TOKEN = os.getenv('GEOCODER_TOKEN')

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
    'английского': 'en', 'английский': 'en'
}


def get_keyboard():
    wether_button = KeyboardButton('☀Моя погода☀', request_location=True)
    my_keboard = ReplyKeyboardMarkup([['🙏Помощь🙏'], [wether_button]], resize_keyboard=True)
    return my_keboard

def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)


    SqlAlchemyBase.metadata.create_all(engine)

async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"👋👋👋Привет {user.mention_html()}! Я бот-помошник для путешествий...\n\n\n❓Чтобы подробнее узнать о моих "
        f"функциях используйте команду /help или нажмите на кнопку «Помошь»❓.",
        reply_markup=get_keyboard())


async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_html(
        "❗В данном сообщении вы можете узнать о всём функционале бота❗\n\n\n"
        "🔸<u><b>Карманный переводчик</b></u>\n"
        "Чтобы получить перевод любого слова или фразы отправте мне собщение со следующим "
        "содержанием:\n<b>Переведи с</b> <i>язык переводимой фразы</i> <b>на</b> <i>язык "
        "результата</i> ...\nПример: Переведи с русского на английский Пирвет мир!\n\n\n"
        "🔸<u><b>Синоптик</b></u>\n"
        "Если вы хотите узнать текущую погоду в городе вашего прибывания нажмите на кнопку "
        "«Моя погода», при этом в чат будет отправлена информация о вашей геолокации.\n\n"
        "Если вас интересует погода в конкретном городе, то отправте мне собщение со "
        "следующим содержанием:\n<b>Погода в городе</b> <i>название города</i>\nПример: "
        "Погода в городе Москва", reply_markup=get_keyboard())


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
    await update.message.reply_html(wether(address["address"].get("city")))


async def echo(update, context):
    global translator, LANGUAGES
    if 'Переведи' in update.message.text:
        try:
            src = LANGUAGES[update.message.text.split()[2]]
            dest = LANGUAGES[update.message.text.split()[4]]
            text = ' '.join(update.message.text.split()[5:])

            await update.message.reply_text(translator.translate(text, src=src, dest=dest).text)
        except Exception as error:
            print(error)
            await update.message.reply_text(
                "Соединение с сервером потеряно. Попробуйте ввести корректные названия языков или подождите немного")

    elif 'Погода в городе' in update.message.text:
        try:
            city = update.message.text.split('Погода в городе ')[-1]
            await update.message.reply_html(wether(city))

        except Exception as error:
            print(error)
            await update.message.reply_text(
                "Соединение с сервером потеряно. Попробуйте ввести корректное название города или подождите немного.")


def main():
    # Запуск бота.
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация комманд.
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex('🙏Помощь🙏'), help_command))
    application.add_handler(MessageHandler(filters.LOCATION, my_wether))
    application.add_handler(MessageHandler(filters.TEXT, echo))

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
