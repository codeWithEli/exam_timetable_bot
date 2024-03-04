import os
import re
import logging
import dotenv
import scraper
from flask import Flask, request

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
SECRET = os.environ['SECRET']
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
Hello {message.from_user.username} 👋,
Welcome to the UG Exams Timetable Bot! 🤖
This bot is designed to assist University of Ghana students 🎓 in finding their exam venues with ease. 

You can search for any course or multiple courses at any time. To search for multiple courses, simply separate each course with a comma. For example: ugbs303, dcit102, ugrc210

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

1. Start by searching for your course using its code. For example, you can type ugbs303 to search for the ugrc210 course.

2. If you want to search for multiple courses at once, simply separate each course code with a comma. For example: ugbs303, dcit102, math306, flaw104

3. The bot will return your exam date 📅, time ⏰, and venue 📍 instantly.

Remember, you can always type /start to get a welcome message, /about to learn more about this bot or /help to get this help message.

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
def handle_single_course_code(message):
    try:

        user_id = str(message.chat.id)

        course_code = message.text.upper().replace(" ", "")

        # Delete previous data from firebase
        FB.delete_exams_details(user_id)

        # Update course code for user
        FB.set_course_code(user_id, course_code)

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
                "📍 Get Exact Venue", callback_data='get_exact_venue'))
            # markup.add(types.InlineKeyboardButton(
            #     "🗓 Create a remmider", callback_data='get_calendar'))

            # Send and delete photo
            with open(screenshot_path, 'rb') as screenshot:
                bot.send_photo(user_id, screenshot)
            bot.send_message(user_id, "I can also help you with 👇👇👇👇",
                             reply_markup=markup)
            os.remove(screenshot_path)
    except Exception as e:
        logger.info(str(e))
        msg = "⚠️ An error occurred ⚠️ \nIf this issue persists, please contact the developer @eli_bigman for assistance. 🙏 "
        # Del sticker and msg
        bot.delete_messages(
            user_id, [sticker_message_id, searching_course_msg])
        # Send error msg
        bot.send_message(
            user_id, msg)
        raise


@bot.message_handler(func=lambda message: re.match(r'^\d{8}$', message.text))
def handle_id(message):
    try:

        user_id = str(message.chat.id)

        user_entered_course_code = FB.get_course_code(user_id)

        if user_entered_course_code is not None and message.text:
            course_code = user_entered_course_code

            ID = int(message.text)

            # Send message
            searching_venue_msg = bot.send_message(
                user_id, "Searching for your venue... 🔍")
            searching_venue_msg_id = searching_venue_msg.message_id

            # Send sticker
            send_sticker = bot.send_sticker(user_id, sticker_id)
            sticker_message_id = send_sticker.message_id

            # Get venue and screenshot
            screenshot_path = scraper.find_exact_exams_venue(
                course_code=course_code, user_id=user_id, ID=ID)

            # Get exact exams venue from firebase
            courses = list(FB.get_saved_exams_details(user_id).keys())

            # remove user_entered_course_code key from courses dict
            key_to_remove = 'user_entered_course_code'
            if key_to_remove in courses:
                courses.remove(key_to_remove)

            # get exact venue from firebase handling cases where batch of courses exist
            exact_venue_list = []

            for course_name in courses:
                exact_venue_list.append(
                    FB.get_exact_venue(user_id, course_name))
                no_id_venues = FB.get_no_id_venues(user_id, course_name)

            # Del sticker
            bot.delete_messages(
                user_id, [sticker_message_id, searching_venue_msg_id])

        else:
            bot.send_message(user_id, "⚠ Please search for a course first")
            logger.info('No course code found')
            FB.set_course_code(user_id, None)
            return

        for exact_venue in exact_venue_list:
            if exact_venue is not None:
                bot.send_message(
                    user_id, f"{course_code} exams venue for ID {ID} is:\n\n📍 {exact_venue} 📍\n\nBest of luck! 🌟")
                with open(screenshot_path, 'rb') as screenshot:
                    bot.send_photo(user_id, screenshot)

                logger.info("FOUND EXACT VENUE ✅")

            elif no_id_venues is not None and exact_venue is None:
                bot.send_message(
                    user_id, f"EXACT EXAMS VENUE FOR {ID} NOT FOUND❗❗\n `Possible venue ⏬⏬\n\nVenues without ID: {('|'.join(no_id_venues))}\n\nPlease check the ID and try agian 🔄")

            else:
                bot.send_message(
                    user_id, f"😞 EXACT EXAMS VENUE NOT FOUND FOR❗❗\n\n {ID} \n\n Please check the ID and try agian 🔄")

        # Delete screenshot
        os.remove(screenshot_path)
        # Set course code to None
        FB.set_course_code(user_id, None)

    except Exception as e:
        msg = "⚠️ An error occurred ⚠️ \nIf this issue persists, please contact the developer @eli_bigman for assistance. 🙏 "
        logger.exception(str(e))
        # Del sticker and msg
        bot.delete_messages(
            user_id, [sticker_message_id, searching_venue_msg_id])
        # Send error msg
        bot.send_message(
            user_id, msg)
        raise


@bot.message_handler(func=lambda message: re.match(r'\b([a-zA-Z]{4}\d{3},\s?)*[a-zA-Z]{4}\d{3}\b', message.text))
def handle_all_course(message):

    try:

        user_id = str(message.chat.id)

        # Delete previous data from firebase
        FB.delete_exams_details(user_id)

        courses = message.text
        cleaned_courses = courses.upper().replace(" ", "").split(",")
        user_courses = ", ".join(cleaned_courses)
        bot.send_message(
            user_id, f"🔍 Searching for {user_courses} ")

        send_sticker = bot.send_sticker(user_id, sticker_id)
        sticker_message_id = send_sticker.message_id

        # Getting course details
        screenshot_path, unavailable_courses = scraper.all_courses_schedule(
            courses, user_id)

        # Delete sticker
        bot.delete_message(user_id, sticker_message_id)

        # Send and delete photo
        with open(screenshot_path, 'rb') as screenshot:
            bot.send_photo(user_id, screenshot)
        os.remove(screenshot_path)

        if len(unavailable_courses) > 0:
            not_found_courses = ", ".join(unavailable_courses)
            bot.send_message(
                user_id, f"Unavailable: {not_found_courses} ❗️❗️ Please double-check the course code \n\nIts possible that these courses have not yet been uploaded to the site 🌐 ( https://sts.ug.edu.gh/timetable/ ) try searching for them at a later time ⏰"
            )

    except Exception as e:
        logger.error(str(e))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id

    if call.data == "get_exact_venue":
        if FB.get_course_code(user_id) is None:
            bot.send_message(user_id,
                             "⚠ Please search for a course first")
        else:
            bot.send_message(user_id, "📍Please enter your ID")


@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.send_message(
        message.chat.id, "Oops! 🙈 Let's try that again. Make sure your course code is on point, like ugrc101 (4 letters, 3 numbers). And hey, don't forget, your ID should be atleast 8 numbers long. Got it? Cool! 😎👍 \nIf issue persists contact my developer @eli_bigman")


if __name__ == "__main__":
    logger.info('Bot is running...')
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5001)))
