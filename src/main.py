import os
import re
import logging
import dotenv
import scraper

import telebot
from telebot import types

# Configure logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]

bot = telebot.TeleBot(TOKEN)

scraper = scraper.Scraper()


@bot.message_handler(commands=['start'])
def start(message):
    """Start command."""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "Exams schedule", callback_data='exams_schedule'))
    markup.add(types.InlineKeyboardButton(
        "Exact exams venue", callback_data='exact_venue'))
    markup.add(types.InlineKeyboardButton(
        "All exams", callback_data='all_exams'))

    bot.send_message(
        message.chat.id,
        f"""
Hello {message.from_user.username},
Welcome to the Exams Timetable Bot! 
This bot helps University of Ghana students 
find their exam venues with ease. 

Get your exam date, time, and venue instantly.
    """, reply_markup=markup
    )


@bot.message_handler(func=lambda message: re.match(r'^[A-Za-z]{4}\d{3}$', message.text))
def handle_course_code(message):
    global course_code
    course_code = message.text.upper().replace(" ", "")
    bot.send_message(
        message.chat.id, f"Searching for {course_code}...")
    screenshot_url = scraper.single_exams_schedule(course_code)

    if screenshot_url is not None:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "Get Exact Venue", callback_data='get_exact_venue'))
        bot.send_photo(message.chat.id, screenshot_url, reply_markup=markup)

    else:
        bot.send_message(
            message.chat.id, f"Sorry {course_code} is not available on the UG timetable site \n https://sts.ug.edu.gh/timetable/ ")
        return


@bot.message_handler(func=lambda message: re.match(r'^\d{8}$', message.text))
def handle_id(message):
    global course_code

    ID = int(message.text)
    bot.send_message(message.chat.id, "Searching for your venue... ")
    venue, screenshot_url = scraper.find_exact_exams_venue(
        course_code=course_code, ID=ID)
    bot.send_message(
        message.chat.id, f"Your exam venue is: {venue} \n All the best ")
    bot.send_photo(message.chat.id, screenshot_url)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "exams_schedule":
        bot.send_message(call.message.chat.id,
                         "Please enter your course code (eg: ugrc101).")
    elif call.data == "exact_venue":
        bot.send_message(call.message.chat.id,
                         "Please enter your course code (eg: ugrc101) and ID.")
    elif call.data == "get_exact_venue":
        bot.send_message(call.message.chat.id, "Please enter your ID.")


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    # This will handle all text messages that don't match the previous handlers
    if re.search(r'^[A-Za-z]{4}\d{3}$', message.text):
        bot.send_message(
            message.chat.id, "Sorry, I didn't understand that. Please enter a valid course code like 'ugrc210'.")
    elif re.search(r'^\d{8}$', message.text):
        bot.send_message(
            message.chat.id, "Sorry, I didn't understand that. Please enter a valid ID of length 8.")
    else:
        bot.send_message(
            message.chat.id, "Sorry, I didn't understand that. Please enter a valid course code or ID.")


if __name__ == "__main__":
    logger.info('Bot is running...')
    bot.infinity_polling()
