import os
import time
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

global sticker_id
sticker_id = "CAACAgUAAxkBAAICWmXNVFmPZfVnlRYbCiLoaC6Ayz80AAJ1AgACrO6pVuBDnskq_U5QNAQ"


@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        f"""
Hello {message.from_user.username} 👋,
Welcome to the UG Exams Timetable Bot! 🤖
This bot is designed to assist University of Ghana students 🎓 in finding their exam venues with ease. 

You can search for any course or multiple courses at any time. To search for multiple courses, simply separate each course with a comma. For example: MATH101, CHEM102, PHYS103

Get your exam date 📅, time ⏰, and venue 📍 instantly. Just type in your course code(s) and let the bot do the rest!

Happy studying and good luck with your exams! 📚🍀

    """
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        f"""
Hello {message.from_user.username} 👋,
Here's how you can use the UG Exams Timetable Bot! 🤖

1. Start by searching for your course using its code. For example, you can type `MATH101` to search for the MATH101 course.

2. If you want to search for multiple courses at once, simply separate each course code with a comma. For example: `MATH101, CHEM102, PHYS103`.

3. The bot will return your exam date 📅, time ⏰, and venue 📍 instantly.

Remember, you can always type `/start` to get a welcome message, or `/about` to learn more about this bot.

Happy studying and good luck with your exams! 📚🍀
        """
    )


@bot.message_handler(commands=['about'])
def about_command(message):
    bot.send_message(message.chat.id,
                     f"""Hello! 👋 This is @eli_bigman. 
I created this Exams Timetable Bot after I nearly missed an exam. 🏃‍♂️💨
This is a simple way to get your exam schedules instantly. Just type in your course code(s), and let the bot handle the rest! 📚🍀 

If you encounter any errors or issues, feel free to reach out. I'm here to help! 🙌

You can also check out the source code for this bot on GitHub: https://github.com/eli-bigman/exam_timetable_bot 💻✨

If you find this bot helpful and want to support my work, you can buy me a coffee ☕️. MOMO => 0551757558.

Enjoy using the bot! 💯"""
                     )


@bot.message_handler(func=lambda message: re.match(r'^[A-Za-z]{4}\s?\d{3}$', message.text))
def handle_course_code(message):
    try:
        global course_code
        course_code = message.text.upper().replace(" ", "")
        bot.send_message(
            message.chat.id, f"🔍 Searching for {course_code}...🚀")

        # sending sticker

        send_sticker = bot.send_sticker(message.chat.id, sticker_id)
        sticker_message_id = send_sticker.message_id

        # Get screenshot for a single exams
        screenshot_path = scraper.single_exams_schedule(course_code)

        # Del sticker
        bot.delete_message(message.chat.id, sticker_message_id)

        if screenshot_path is None:
            bot.send_message(
                message.chat.id, f"Couldn't find {course_code} ❗️❗️❗️\nPlease double-check the course codes\n\nIts possible that this course has not yet been uploaded to the site 🌐\n( https://sts.ug.edu.gh/timetable/ ) \ntry searching for them at a later time ⏰")
            return

        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "📍 Get Exact Venue", callback_data='get_exact_venue'))
            # markup.add(types.InlineKeyboardButton(
            #     "🗓 Create a remmider", callback_data='get_exact_venue'))

            with open(screenshot_path, 'rb') as screenshot:
                bot.send_photo(message.chat.id, screenshot)
            bot.send_message(message.chat.id, "I can also help you 👇👇👇👇👇👇",
                             reply_markup=markup)
    except Exception as e:
        logger.info(str(e))


@bot.message_handler(func=lambda message: re.match(r'^\d{8}$', message.text))
def handle_id(message):
    try:
        global course_code

        ID = int(message.text)

        if not course_code:
            bot.send_message(
                message.chat.id, "⚠ Please search for a course first")

        else:
            bot.send_message(message.chat.id, "Searching for your venue... 🔍")

            send_sticker = bot.send_sticker(message.chat.id, sticker_id)
            sticker_message_id = send_sticker.message_id

            # Get venue and screenshot
            venue, screenshot_path = scraper.find_exact_exams_venue(
                course_code=course_code, ID=ID)

            # Del sticker
            bot.delete_message(message.chat.id, sticker_message_id)

            if venue is None:
                bot.send_message(
                    message.chat.id, f"😞 NO EXAMS VENUE FOUND❗❗\n\n {ID} \n\n Please check the ID and try agian 🔄")
            else:
                bot.send_message(
                    message.chat.id, f"Your exam venue is : \n\n📍 {venue} 📍\n\nBest of luck! 🌟")
                with open(screenshot_path, 'rb') as screenshot:
                    bot.send_photo(message.chat.id, screenshot)
                os.remove(screenshot_path)
    except Exception as e:
        logger.exception(str(e))


@bot.message_handler(func=lambda message: re.match(r'\b([a-zA-Z]{4}\d{3},\s?)*[a-zA-Z]{4}\d{3}\b', message.text))
def handle_all_course(message):
    try:
        courses = message.text
        cleaned_courses = courses.upper().replace(" ", "").split(",")
        bot.send_message(
            message.chat.id, f"🔍 Searching for {cleaned_courses} ")

        send_sticker = bot.send_sticker(message.chat.id, sticker_id)
        sticker_message_id = send_sticker.message_id

        # Getting course details
        screenshot_path, unavailable_courses = scraper.all_courses_schedule(
            courses)

        # Del sticker
        bot.delete_message(message.chat.id, sticker_message_id)

        with open(screenshot_path, 'rb') as screenshot:
            bot.send_photo(message.chat.id, screenshot)
        # bot.send_photo(message.chat.id, screenshot_path)
        os.remove(screenshot_path)

        if len(unavailable_courses) > 0:
            bot.send_message(
                message.chat.id, f"Unavailable: {unavailable_courses} ❗️❗️ Please double-check the course code \n\nIts possible that these courses have not yet been uploaded to the site 🌐 ( https://sts.ug.edu.gh/timetable/ ) try searching for them at a later time ⏰")

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


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.send_message(
        message.chat.id, "Sorry, I didn't understand that 😕 \nPlease enter a valid course code 📚 \nConsiting of 4 letters and 3 numbers like ugrc101 ")


if __name__ == "__main__":
    logger.info('Bot is running...')
    bot.infinity_polling()
