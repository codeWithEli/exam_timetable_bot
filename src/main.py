import os
import time
import re
import logging
import dotenv
import scraper


import telebot
from telebot import types

from firebase_functions import delete_from_firebase

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
        "Exam Schedule", callback_data='exams_schedule'))
    markup.add(types.InlineKeyboardButton(
        "All exams", callback_data='all_exams'))

    bot.send_message(
        message.chat.id,
        f"""
Hello {message.from_user.username} 👋,
Welcome to the Exams Timetable Bot! 🤖
This bot is designed to assist University of Ghana students 🎓 in finding their exam venues with ease. 

You can search for any course or multiple courses at any time. To search for multiple courses, simply separate each course with a comma. For example: MATH101, CHEM102, PHYS103

Get your exam date 📅, time ⏰, and venue 📍 instantly. Just type in your course code(s) and let the bot do the rest!

Happy studying and good luck with your exams! 📚🍀

    """, reply_markup=markup
    )


@bot.message_handler(commands=['about'])
def about_command(message):
    bot.send_message(message.chat.id,
                     "Hello! This is @eli_bigman. I created this Exams Timetable Bot after I nearly missed an exam. I wanted to make sure that no other student has to go through that stress. So, here's a simple way for all of us at the University of Ghana to get our exam schedules instantly. Just type in your course code(s), and let the bot handle the rest! 📚🍀 If you encounter any errors or issues, feel free to reach out. I'm here to help!")


@bot.message_handler(func=lambda message: re.match(r'^[A-Za-z]{4}\d{3}$', message.text))
def handle_course_code(message):
    global course_code
    course_code = message.text.upper().replace(" ", "")
    bot.send_message(
        message.chat.id, f"🔍 Searching for {course_code}...🚀")

    # sending sticker
    sticker_id = "CAACAgUAAxkBAAICWmXNVFmPZfVnlRYbCiLoaC6Ayz80AAJ1AgACrO6pVuBDnskq_U5QNAQ"

    send_sticker = bot.send_sticker(message.chat.id, sticker_id)
    sticker_message_id = send_sticker.message_id

    # Get screenshot for a single exams
    screenshot_url = scraper.single_exams_schedule(course_code)

    # Del sticker
    bot.delete_message(message.chat.id, sticker_message_id)

    if screenshot_url is None:
        bot.send_message(
            message.chat.id, f"Unavailable: {course_code} ❗️\nIts possible that these courses have not yet been uploaded to the site 🌐 ( https://sts.ug.edu.gh/timetable/ ) Please double-check the course codes or try searching for them at a later time ⏰")
        return

    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "📍 Get Exact Venue", callback_data='get_exact_venue'))
        markup.add(types.InlineKeyboardButton(
            "🗓 Create a remmider", callback_data='get_exact_venue'))
        bot.send_photo(message.chat.id, screenshot_url)
        bot.send_message(message.chat.id, "I can help you 👇👇👇👇👇👇👇👇",
                         reply_markup=markup)


@bot.message_handler(func=lambda message: re.match(r'^\d{8}$', message.text))
def handle_id(message):
    global course_code
    ID = int(message.text)

    bot.send_message(message.chat.id, "Searching for your venue... 🔍")
    # sending sticker
    sticker_id = "CAACAgUAAxkBAAICWmXNVFmPZfVnlRYbCiLoaC6Ayz80AAJ1AgACrO6pVuBDnskq_U5QNAQ"

    send_sticker = bot.send_sticker(message.chat.id, sticker_id)
    sticker_message_id = send_sticker.message_id

    # Get venue and screenshot
    venue, screenshot_url = scraper.find_exact_exams_venue(
        course_code=course_code, ID=ID)

    # Del sticker
    bot.delete_message(message.chat.id, sticker_message_id)

    if venue is None:
        bot.send_message(
            message.chat.id, f"😞 Sorry NO EXAMS VENUE FOUND \n\n {ID} \n\n Please check the ID and try agian 🔄")
    else:
        bot.send_message(
            message.chat.id, f"Your exam venue is: \n\n📍 {venue} 📍\n\nBest of luck! 🌟")
        bot.send_photo(message.chat.id, screenshot_url)


@bot.message_handler(func=lambda message: re.match(r'\b([a-zA-Z]{4}\s?\d{3},\s?)*[a-zA-Z]{4}\s?\d{3}\b', message.text))
def handle_all_course(message):
    try:
        courses = message.text
        cleaned_courses = courses.upper().replace(" ", "").split(",")
        bot.send_message(
            message.chat.id, f"🔍 Searching for {cleaned_courses} ")

        # sending sticker
        sticker_id = "CAACAgUAAxkBAAICWmXNVFmPZfVnlRYbCiLoaC6Ayz80AAJ1AgACrO6pVuBDnskq_U5QNAQ"

        send_sticker = bot.send_sticker(message.chat.id, sticker_id)
        sticker_message_id = send_sticker.message_id

        # Getting course details
        screenshot_url, unavailable_courses = scraper.all_courses_schedule(
            courses)

        # Del sticker
        bot.delete_message(message.chat.id, sticker_message_id)

        bot.send_photo(message.chat.id, screenshot_url)
        if len(unavailable_courses) > 0:
            bot.send_message(
                message.chat.id, f"Unavailable: {unavailable_courses} ❗️\nIts possible that this course has not yet been uploaded to the site 🌐 ( https://sts.ug.edu.gh/timetable/ ) Please double-check the course code or try searching for them at a later time ⏰")

    except Exception as e:
        logger.error(str(e))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "exams_schedule":
        bot.send_message(call.message.chat.id,
                         "📚 Please enter your course code (eg: ugrc101).")
    elif call.data == "get_exact_venue":
        bot.send_message(call.message.chat.id, "📍Please enter your ID")
    elif call.data == "all_exams":
        bot.send_message(
            call.message.chat.id, "📚 Please enter your course codes, separate with commas 👍"
        )


@bot.message_handler(content_types=['sticker'])
def sticker_id(message):
    print('Sticker ID:', message.sticker.file_id)


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.send_message(
        message.chat.id, "Sorry, I didn't understand that 😕 \nPlease enter a valid course code 📚 \nConsiting of 4 letters and 3 numbers like ugrc101 ")


if __name__ == "__main__":
    logger.info('Bot is running...')
    bot.infinity_polling()
