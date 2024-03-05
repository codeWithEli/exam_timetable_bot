import os
import re
import logging
import dotenv
import scraper
from flask import Flask, request
# from prettytable import PrettyTable

import telebot
from telebot import types

import firebase_functions as FB

# Configure logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

dotenv.load_dotenv()
TOKEN = os.environ["BOT_TOKEN"]

bot = telebot.TeleBot(TOKEN)

# Create Scraper class instance
scraper = scraper.Scraper()

global sticker_id
sticker_id = "CAACAgUAAxkBAAICWmXNVFmPZfVnlRYbCiLoaC6Ayz80AAJ1AgACrO6pVuBDnskq_U5QNAQ"

# Set up flask webhook
app = Flask(__name__)

bot.remove_webhook()
URL = os.environ['RENDER_URL']
ngrok_URL = os.environ['NGROK']
bot.set_webhook(url=URL)


@app.route('/', methods=['POST'])
def webhook():
    updates = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8"))
    bot.process_new_updates([updates])
    return "ok", 200


@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        f"""
Greetings {message.from_user.username} 👋, I am your Exams Bot! 🤖

I am programmed to make your exam scheduling easier. Here's how I can assist you:

1. Single course search example: \n\nUGRC102 or UGRC102, 10234567

2. Multiple courses search example: \n\nUGBS303, DCIT102, MATH306 or UGBS303, DCIT102, MATH306, 10234567

3. I will return your exam date 📅, time ⏰, and venue (exact venue) 📍 instantly.

Simply input your course code(s) and/or ID, and leave the rest to me!

Happy studying and good luck with your exams! 📚🍀

    """
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        f"""
Hello {message.from_user.username} 
How to use your Exams Bot! 🤖

1. Single course search example: \n\nugbs303 or ugbs303, 10234567

2. Multiple courses search example: \n\nugbs303, dcit102, math306 or ugbs303, dcit102, math306, 10234567\n

3. I will return your exam date 📅, time ⏰, and venue (exact venue) 📍 instantly.

Remember, you can always type /start to get a welcome message, /about to learn more about me or /help to get this help message.

Happy studying and good luck with your exams! 📚🍀
        """
    )


@bot.message_handler(commands=['about'])
def about_command(message):
    bot.send_message(message.chat.id,
                     f"""Hello! 👋 This is @eli_bigman. 
I created this Exams Timetable Bot after I nearly missed an exam. 🏃‍♂️💨
This is a simple way to get your exam schedules instantly. Just type in your course code(s), and let the bot handle the rest! 📚🍀 

If you encounter any errors or issues, feel free to reach out (@eli_bigman). I'm here to help! 🙌

You can also check out the source code for this bot on GitHub: https://github.com/exam_timetable_bot 💻✨

If you find this bot useful and wish to show your support, contributions towards hosting costs or a coffee for the developer are greatly appreciated ☕️. 
You can send your support via MOMO at 0551757558. Thank you! 😊 

Enjoy using the bot! 💯"""
                     )


@bot.message_handler(func=lambda message: re.match(r'^[A-Za-z]{4}\s?\d{3}$', message.text))
def handle_single_course_code(message):
    try:

        user_id = str(message.chat.id)

        course_code = message.text.upper().replace(" ", "")

        # Delete previous data from firebase
        FB.delete_exams_details(user_id)

        searching_course_msg = bot.send_message(
            user_id, f"🔍 Searching for {course_code}...🚀")
        searching_course_msg_id = searching_course_msg.message_id

        # sending sticker
        send_sticker = bot.send_sticker(user_id, sticker_id)
        sticker_message_id = send_sticker.message_id

        # Get screenshot for a single exams
        screenshot_path = scraper.single_exams_schedule(course_code, user_id)

        # Del searching message and sticker
        bot.delete_messages(
            user_id, [searching_course_msg_id, sticker_message_id])

        if screenshot_path is None:
            bot.send_message(
                user_id, f"Couldn't find {course_code} ❗️❗️❗️\nPlease double-check the course codes\n\nIts possible that this course has not yet been uploaded to the site 🌐\n( https://sts.ug.edu.gh/timetable/ ) \ntry searching for them at a later time ⏰")
            return

        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "🗓 Create a remmider", callback_data='get_calendar'))

            # Send and delete photo
            with open(screenshot_path, 'rb') as screenshot:
                bot.send_photo(user_id, screenshot)
            bot.send_message(
                user_id, f"To find your exact venue 📍 for {course_code}, simply add your ID at the end. \nFor example: {course_code}, 10223159" ,reply_markup=markup)

            os.remove(screenshot_path)
            return

    except Exception as e:
        logger.info(str(e))
        msg = "⚠️ An error occurred ⚠️ \nIf this issue persists, please contact my developer @eli_bigman for assistance. 🙏 "
        # Del sticker and msg
        bot.delete_messages(
            user_id, [sticker_message_id, searching_course_msg])
        # Send error msg
        bot.send_message(
            user_id, msg)
        raise


@bot.message_handler(func=lambda message: re.match(r"^([a-zA-Z]{4}\s?\d{3}\s?,\s?)+([a-zA-Z]{4}\s?\d{3}|\s?[0-9]{8,})$", message.text))
def handle_course_with_ID(message):

    try:
        logger.info(f'User sent --- {message.text}')
        user_id = str(message.chat.id)
        # Delete previous data from firebase
        FB.delete_exams_details(user_id)

        ID = None
        user_search_text = message.text
        student_id = re.findall(r'\d+$', user_search_text)
        if student_id:
            ID = int(student_id[0])
            user_search_text = re.sub(r',\s?\d+', "", user_search_text)
            courses = user_search_text
            logger.info(
                f"ID provided {ID} for all course seacrch {user_search_text} ")

        else:
            courses = user_search_text
            logger.info("No id provided for course seacrch")

        cleaned_courses = courses.upper().replace(" ", "").split(",")
        user_courses = ", ".join(cleaned_courses)

        searching_all_courses = bot.send_message(
            user_id, f"🔍 Searching for {user_courses} ")
        searching_all_courses_id = searching_all_courses.message_id

        send_sticker = bot.send_sticker(user_id, sticker_id)
        sticker_message_id = send_sticker.message_id

        # Getting course details
        screenshot_path, unavailable_courses = scraper.all_courses_schedule(
            courses, user_id, ID)

        # Create table
        # schedule_table = PrettyTable(['Course','Exact Venue', 'No ID Venue'])

        # for
        # Delete sticker and searching msg
        bot.delete_messages(
            user_id, [sticker_message_id, searching_all_courses_id])

        # Send and delete photo
        with open(screenshot_path, 'rb') as screenshot:
            bot.send_photo(user_id, screenshot)
        os.remove(screenshot_path)

        if len(unavailable_courses) > 0:
            not_found_courses = ", ".join(unavailable_courses)
            bot.send_message(
                user_id, f"Unavailable: {not_found_courses} ❗️❗️ Please double-check the course code \n\nIts possible that these courses have not yet been uploaded to the UG website 🌐 ( https://sts.ug.edu.gh/timetable/ ) try searching for them at a later time ⏰"
            )

        if ID is None:
            bot.send_message(
                user_id, "Want your exact venue? Simply add your ID at the end of the course code. For example: ugbs303, dcit303, ugrc210, 10223111 ")

    except Exception as e:
        logger.error(str(e))
        msg = "⚠️ An error occurred ⚠️ \nIf this issue persists, please contact the developer @eli_bigman for assistance. 🙏 "
        # Del sticker and msg
        bot.delete_messages(
            user_id, [sticker_message_id, searching_all_courses_id])
        # Send error msg
        bot.send_message(user_id, msg)
        raise


# @bot.callback_query_handler(func=lambda call: True)
# def callback_query(call):
#     user_id = call.message.chat.id

#     # if call.data == "get_exact_venue":
#     #     if FB.get_course_code(user_id) is None:
#     #         bot.send_message(user_id,
#     #                          "⚠ Please search for a course first")
#     #     else:
#     #         bot.send_message(user_id, "📍Please enter your ID")


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.send_message(
        message.chat.id, f"{message.text} \nOops! 😕 Pls make sure your course code is correct, like ugrc101 (4 letters, 3 numbers). And also, your ID should be atleast 8 numbers long. Got it? Cool! 😎👍 \nLet's try that again.\nIf issue persists contact my developer @eli_bigman")


if __name__ == "__main__":
    logger.info('Bot is running...')
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5001)))
