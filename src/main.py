import logging
import os
import dotenv
import asyncio
import re

from aiohttp import web

import scraper
import firebase_functions as FB

from aiogram import Bot, Dispatcher, Router, types, F, exceptions
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Configure logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Get environment variables
dotenv.load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")
BASE_WEBHOOK_URL = os.environ.get("WEBHOOK")
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.environ.get("PORT"))


# All handlers should be attached to the Router (or Dispatcher)
router = Router()

# Create a bot instance
bot = Bot(TOKEN)

# Create scraper an instance of the scraper class
scraper = scraper.Scraper()

# pepe frog sticker id
sticker_id = "CAACAgUAAxkBAAICWmXNVFmPZfVnlRYbCiLoaC6Ayz80AAJ1AgACrO6pVuBDnskq_U5QNAQ"


# Store each user's create calendar buttom id
create_calendar_buttom_id = {}


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        f"""
Greetings {message.from_user.username} 👋, Welcome to your Exams Bot! 🤖

I am programmed to make your exam scheduling easier. Here's how I can assist you:

1. Single course search example: \n\nUGRC102 or UGRC102, 10234567

2. Multiple courses search example: \n\nUGBS303, DCIT102, MATH306 or UGBS303, DCIT102, MATH306, 10234567

3. I will return your exam date 📅, time ⏰, and venue (exact venue) 📍 instantly.

Simply input your course code(s) and/or ID, and leave the rest to me!

Happy studying and good luck with your exams! 📚🍀

    """
    )


@router.message(Command('help'))
async def command_help_handler(message: Message) -> None:
    await message.answer(f"""
Hello {message.from_user.username}, 
Here is how to use your Exams Bot! 🤖

1. Single course search example: \n\nugbs303 or ugbs303, 10234567

2. Multiple courses search example: \n\nugbs303, dcit102, math306 \nOR \nugbs303, dcit102, math306, 10234567\n

3. I will return your exam date 📅, time ⏰, and venue (exact venue) 📍 instantly.

Remember, you can always type /start to get a welcome message, /about to learn more about me or /help to get this help message.

Happy studying and good luck with your exams! 📚🍀
        """)


@router.message(Command('about'))
async def command_about_handler(message: Message) -> None:
    await message.answer(
        f"""
Hello! 👋 This is @eli_bigman
I created this Exams Timetable Bot after I nearly missed an exam. 🏃‍♂️💨
This is a simple way to get your exam schedules instantly. Just type in your course code(s), and let the bot handle the rest!

If you encounter any errors or issues, feel free to reach out (@eli_bigman). I'm here to help! 🙌

You can also check out the source code for this bot on GitHub: https://github.com/exam_timetable_bot 💻✨

If you find this bot useful and wish to show your support, contributions towards hosting costs or a coffee for the developer are greatly appreciated ☕️.
You can send your support via MOMO at 0551757558. Thank you!

Enjoy using the bot! 💯
""")


@router.message(F.text.regexp(r'^[A-Za-z]{4}\s?\d{3}$'))
async def handle_single_course_code(message: types.Message):
    """
    This handler single course code search without student ID 
    """
    try:
        user_id = await get_chat_id(message)
        course_code = await get_course_code(message)

        # Delete create calendar buttom
        buttom_id = create_calendar_buttom_id.get(user_id)
        if buttom_id is not None:
            buttom_id = int(buttom_id)
            reply_msg = await bot.edit_message_reply_markup(
                user_id, message_id=buttom_id, reply_markup=None)

        searching_course_msg = await bot.send_message(
            user_id, f" Searching for {course_code}...")
        searching_course_msg_id = searching_course_msg.message_id

        # sending sticker
        send_sticker = await bot.send_sticker(chat_id=user_id, sticker=sticker_id)
        sticker_message_id = send_sticker.message_id

        # Get screenshot for a single exams
        image_url = scraper.single_exams_schedule(
            course_code=course_code, user_id=user_id)

        # Del searching message and sticker
        await bot.delete_messages(
            user_id, [sticker_message_id, searching_course_msg_id])

        if image_url is None:
            await bot.send_message(
                user_id, f"Couldn't find {course_code} ❗️❗️❗️\nPlease double-check the course codes\n\nIts possible that this course has not yet been uploaded to the site \n( https://sts.ug.edu.gh/timetable/ ) \ntry searching for them at a later time ⏰")
            return

        else:
            builder = InlineKeyboardBuilder()
            builder.button(
                text="Create a remmider ⏰", callback_data='get_calendar')

            markup = builder.as_markup()

            await bot.send_photo(user_id, image_url)
            reply_msg = await bot.send_message(
                user_id, f"To find your exact venue 📍 for {course_code}, simply add your ID at the end. \nFor example: {course_code}, 10223159 📝", reply_markup=markup)
            create_calendar_buttom_id[user_id] = reply_msg.message_id

            return

    except Exception as e:
        logger.info(str(e))
        msg = "⚠️ An error occurred ⚠️ \nIf this issue persists, please contact my developer @eli_bigman for assistance.  "
        # Del sticker and msg
        await bot.delete_messages(
            user_id, [sticker_message_id, searching_course_msg_id])
        # Send error msg
        await bot.send_message(
            user_id, msg)
        raise


@router.message(F.text.regexp(r'^([a-zA-Z]{4}\s?\d{3}\s?,\s?)+([a-zA-Z]{4}\s?\d{3}|\s?[0-9]{8,})$'))
async def handle_course_with_ID(message: types.Message):
    """
    Processes messages with course codes and optional student ID to fetch exam schedules. 
    Cleans data, searches schedules, and manages user interactions. Logs and reports errors.
    """
    try:
        logger.info(f'User sent --- {message.text}')
        user_id = str(await get_chat_id(message))
        # Delete previous data from firebase
        # FB.delete_exams_details(user_id)

        ID = None
        user_search_text = await get_search_text(message)
        student_id = re.findall(r'\d+$', user_search_text)
        if student_id:
            ID = int(student_id[0])
            user_search_text = re.sub(r',\s?\d+', "", user_search_text)
            courses = user_search_text
            logger.info(
                f"ID provided {ID} for all course seacrch {courses} ")

        else:
            courses = user_search_text
            logger.info("No id provided for course seacrch")

        cleaned_courses = courses.upper().replace(" ", "").split(",")
        user_courses = ", ".join(cleaned_courses)

        searching_all_courses = await bot.send_message(
            user_id, f"🔍 Searching for {user_courses} ")
        searching_all_courses_id = searching_all_courses.message_id

        send_sticker = await bot.send_sticker(user_id, sticker_id)
        sticker_message_id = send_sticker.message_id

        # Getting course details
        image_url, unavailable_courses = scraper.all_courses_schedule(
            courses, user_id, ID)

        # Delete sticker and searching msg
        await bot.delete_messages(
            user_id, [sticker_message_id, searching_all_courses_id])

        # Create calendar button
        builder = InlineKeyboardBuilder()
        builder.button(
            text="Create a remmider ⏰", callback_data='get_calendar')

        markup = builder.as_markup()

        # Send and delete photo
        await bot.send_photo(user_id, image_url, reply_markup=markup)

        # Delete screenshot from firebase
        if len(unavailable_courses) > 0:
            not_found_courses = ", ".join(unavailable_courses)
            await bot.send_message(
                user_id, f"⚠️ Couldn't find : {not_found_courses} ❗️❗️\nPlease double-check the course code \n\nIts highly possible that these courses have not yet been uploaded to the UG website 🌐 ( https://sts.ug.edu.gh/timetable/ ) try searching for them at a later time ⏰"
            )

        if ID is None:
            await bot.send_message(
                user_id, "Want your exact venue? Simply add your ID at the end of the course code. For example: ugbs303, dcit303, ugrc210, 10223111 ")

    except Exception as e:
        logger.error(str(e))
        msg = "⚠️ An error occurred ⚠️ \nIf this issue persists, please contact the developer @eli_bigman for assistance. 🙏 "
        # Del sticker and msg
        await bot.delete_messages(
            user_id, [sticker_message_id, searching_all_courses_id])
        # Send error msg
        await bot.send_message(user_id, msg)
        raise


async def get_search_text(message):
    searched_text = message.text
    return searched_text


async def get_course_code(message):
    course_code = message.text.upper().replace(" ", "")
    return course_code


async def get_chat_id(message: types.Message):
    chat_id = str(message.chat.id)
    return chat_id


@router.message()
async def handle_unmatched_messages(message: types.Message):
    await message.answer(
        f"""
{message.text} \nOops! 😕 Please ensure that your course code consists of 4 letters followed by 3 numbers 📚. 
Additionally, your ID should be at least 8 numbers long 🔢. Separate them with a comma, like this: ugrc210, 10921287.
\nLet's try that again 🔄.\n\nIf this issue persists, please contact my developer @eli_bigman
""")


async def on_startup(bot: Bot) -> None:
    try:
        await bot.set_webhook(f"{BASE_WEBHOOK_URL}")
    except exceptions.TelegramRetryAfter as e:
        await asyncio.sleep(e.timeout)
        await bot.set_webhook(f"{BASE_WEBHOOK_URL}")


def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)
    dp.startup.register(on_startup)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )

    webhook_requests_handler.register(app, path="/")
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)



if __name__ == "__main__":
    logger.info(f"WEBHOOK_URL--{BASE_WEBHOOK_URL}")
    main()
