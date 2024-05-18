import logging
import os
import dotenv
import asyncio
import re

from aiohttp import web

import scraper
# import firebase_functions as FB
from firebase_helper_functions import FirebaseHelperFunctions
from find_single_exam import main as FEVmain

from aiogram import Bot, Dispatcher, Router, types, F, exceptions
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums.parse_mode import ParseMode

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
WEB_SERVER_PORT = int(os.environ.get("PORT", 8000))
DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID")

router = Router(name=__name__)

# Create a bot instance
bot = Bot(TOKEN)

# Create scraper an instance of the scraper class
scraper = scraper.Scraper()

# pepe frog sticker id
sticker_id = "CAACAgUAAxkBAAICWmXNVFmPZfVnlRYbCiLoaC6Ayz80AAJ1AgACrO6pVuBDnskq_U5QNAQ"


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with /start command
    """
    await message.answer(
        f"""
Greetings {message.from_user.username}👋, Welcome to your Exams Bot! 🤖

You can search for a any exams schedule

1. Search example: ugrc102, 10234567

2. I will return your exams venue (exact venue) 📍, exam date 📅 and time ⏰  instantly from https://sts.ug.edu.gh/timetable/.

Simply input your course code and ID, and leave the rest to me!

Happy studying and good luck with your exams! 📚🍀

    """
    )


@router.message(Command('help'))
async def command_help_handler(message: Message) -> None:
    await message.answer(f"""
Hello {message.from_user.username}, 
Here is how to use your Exams Bot! 🤖

You can search for course any exams schedule

1. Search examples: ugrc102, 10234567

2. I will return your exams venue (exact venue) 📍, exam date 📅 and time ⏰  instantly from https://sts.ug.edu.gh/timetable/.

Remember, you can always type /start to get a welcome message, /about to learn more about me or /help to get this help message.

Happy studying and good luck with your exams! 📚🍀
        """)


@router.message(Command('about'))
async def command_about_handler(message: Message) -> None:
    await message.answer(
        f"""
Hello! 👋 This is @eli_bigman
I created this Exams Timetable Bot after I nearly missed an exam. 🏃‍♂️💨
This is a simple way to get your exam schedules instantly. Just type in your course code, and let the bot handle the rest!

If you encounter any errors or issues, feel free to reach out 🙌

You can also check out and star the source code for this bot on GitHub: https://github.com/eli-bigman/exam_timetable_bot 💻✨

If you find this bot useful and wish to show your support, contributions towards hosting costs or a coffee for the developer are greatly appreciated ☕️.
You can send your support via MOMO at 0551757558. Thank you!

Enjoy using the bot! 💯
""")


@router.message(F.text.regexp(r'^([a-zA-Z]{4}\s?\d{3}\s?,\s?)(\s?[0-9]{8,})$'))
@profile
async def handle_exam_schedules_search(message: types.Message):
    """
    This handler single course search with student ID 
    """
    try:
        user_id = str(await get_chat_id(message))

        #initialize firebase helper functions
        firebase = FirebaseHelperFunctions(user_id)

        ID = None
        user_search_text = await get_search_text(message)
        student_id = re.findall(r'\d+$', user_search_text)

        # Get student ID from user querry
        ID = int(student_id[0])
        user_search_text = re.sub(r',\s?\d+\s?', "", user_search_text)
        course_code = user_search_text.strip().upper()

        searching_course_msg = await bot.send_message(
            user_id, f"🔎 Searching for {course_code}...🚀")
        searching_course_msg_id = searching_course_msg.message_id

        # sending sticker
        send_sticker = await bot.send_sticker(chat_id=user_id, sticker=sticker_id)
        sticker_message_id = send_sticker.message_id

        # Get exams links for a single exams
        links = scraper.single_exams_schedule(course_code)

        if links:
            found_exact_venue = await FEVmain(user_id, ID, links)
            # exams_details = FB.get_saved_exams_details(user_id)
        else:
            await bot.delete_messages(
                user_id, [sticker_message_id, searching_course_msg_id])
            err_response=f"""<strong>❌ {course_code} not found on UG timetable site</strong>
Please double-check the course code.\n
It's possible that <strong>{course_code}</strong> has not yet been uploaded to the site yet. You can try searching for it at a later time.

<i><a href="https://sts.ug.edu.gh/timetable/">Visit UG timetable site 🌍</a></i>
"""
            await message.reply(
                text=err_response, parse_mode=ParseMode.HTML)

            return

        if found_exact_venue:
            exact_venues_key_list = firebase.get_exact_venue_keys()
            await message.reply(f"Found {len(exact_venues_key_list)} venue(s)📍 for ID {ID} \n\nPLEASE CONFIRM YOUR CAMPUS IN THE LINK 🌍")

            for course in exact_venues_key_list:
                info = firebase.get_exact_venue_info(course)
                # info = exams_details.get(course, [])
                response = f"""
<strong>Link <a href="{info.get("Link")}">{"👉"}{info.get("Full_Course_Name")}{"🌍"}</a></strong>
<blockquote>
<strong>Course_Level</strong> : {info.get("Course_Level")}\n
<strong>Course Name</strong> : {info.get("Full_Course_Name")}\n
<strong>Exams Date</strong> : {info.get("Exams_Date")}\n
<strong>Exams Time</strong> : {info.get("Exams_Time")}\n
<strong>📌 Exact Venue for {ID} </strong> : <code>{info.get("Exact_Venue")}</code>\n
<strong>Exams Status</strong> : <i>{info.get("Exams_Status")}</i>\n
<strong>Venues without IDs</strong> : {info.get("No_ID_Venue")}\n
</blockquote>
<strong>❗ PLEASE CONFIRM YOUR CAMPUS IN THE LINK ABOVE CLICK ON IT TO VERIFY 💯 </strong>

"""

                await bot.delete_messages(
                    user_id, [sticker_message_id, searching_course_msg_id])
                await message.answer(text=response, parse_mode=ParseMode.HTML)

        elif not found_exact_venue:
            not_exact_venues_key_list = firebase.get_not_exact_venue_keys()
            await message.reply(f"❗No exact venue found for ID - {ID}! ❗\n\nHowever, I've discovered {len(not_exact_venues_key_list)} exam schedule(s) for {course_code}.")

            for course in not_exact_venues_key_list:
                info = firebase.get_not_exact_venue_info(course)
                # info = exams_details[course]
                all_exams_venues = '\n📍'.join(info.get("All_Exams_Venues", []))

                response = f"""
<strong>Link <a href="{info.get("Link")}">{"👉"}{info.get("Full_Course_Name")}{"🌍"}</a></strong>
<blockquote>
<strong>Course_Level</strong> : {info.get("Course_Level")}\n
<strong>Course Name</strong> : {info.get("Full_Course_Name")}\n
<strong>Exams Date</strong> : {info.get("Exams_Date")}\n
<strong>Exams Time</strong> : {info.get("Exams_Time")}\n
<strong>Exams Status</strong> : <i>{info.get("Exams_Status")}</i>\n
<strong>All Exams Venue</strong> :\n{"📍"}{all_exams_venues}\n
</blockquote>

"""
                await bot.delete_messages(
                    user_id, [sticker_message_id, searching_course_msg_id])
                await message.answer(text=response, parse_mode=ParseMode.HTML)

        return

    except Exception as e:
        logger.info(str(e))
        error_msg = str(e)
        msg = "⚠️ An error occurred ⚠️ \nIf this issue persists, please contact my developer @eli_bigman for assistance."
        await bot.delete_messages(
            user_id, [sticker_message_id, searching_course_msg_id])
        await message.reply(
            user_id, msg)
        if DEVELOPER_CHAT_ID:
            await bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=f"An error occured: \n{error_msg}")
        raise


def calendar_button():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Create a remmider ⏰", callback_data='get_calendar')

    return builder.as_markup()


def alarm_offset_button():
    """Inline keyboard with alarm offset options."""
    keyboard = InlineKeyboardBuilder()
    offset_options = [("30 min", "30"), ("1 hr", "60"), ("2 hr",
                                                         "120"), ("4 hr", "240")]
    for text, callback_data in offset_options:
        keyboard.button(text=text, callback_data=callback_data)
    return keyboard.as_markup()


@router.callback_query(lambda c: c.data == "get_calendar")
async def handle_buttoms(call: types.callback_query):

    await call.message.edit_reply_markup(text=f"{Message}\nPlease pick a time delay for the calender", reply_markup=alarm_offset_button())

    await call.answer("Please pick a time delay for the calender")


@router.callback_query(lambda c: c.data in ["30", "60", "120", "240"])
async def handle_buttoms(call: types.callback_query):

    alarm_offset = call.data

    if alarm_offset == "30":
        await call.message.edit_reply_markup("30", reply_markup=None)
    elif alarm_offset == "60":
        await call.message.edit_reply_markup("60", reply_markup=None)
    elif alarm_offset == "120":
        await call.message.edit_reply_markup("120", reply_markup=None)
    elif alarm_offset == "240":
        await call.message.edit_reply_markup("240", reply_markup=None)
    call.answer("Generating calender....")


async def get_search_text(message):
    searched_text = message.text
    return searched_text


async def get_course_code(message):
    course_code = message.text.upper().replace(" ", "")
    return course_code


async def get_chat_id(message: types.Message):
    chat_id = str(message.chat.id)
    return chat_id


@router.message(lambda message: message.text.lower() == 'up?')
async def handle_are_you_up(message: types.Message):
    response = "Who needs sleep when you’re a bot? I’m here and ready to assist! 🌞"
    await message.reply(response)


@router.message()
async def handle_unmatched_messages(message: types.Message):
    await message.reply(
        f"""
Oops!😕 
Pleae ensure course code has 4 letters and 3 numbers 📚
ID should be at least 8 numbers 🔢
Separate with a comma, like: ugrc210, 10921287.
\nLet's try that again 🔄.\n\nIf this issue persists, please contact my developer @eli_bigman
""")


async def on_startup(bot: Bot) -> None:
    try:
        # Delete and set webhook
        await bot.delete_webhook(drop_pending_updates=False)
        await bot.set_webhook(f"{BASE_WEBHOOK_URL}")

    except exceptions.TelegramRetryAfter as e:
        # if too many request at a time sleep and try again
        await asyncio.sleep(e.timeout)
        await bot.set_webhook(f"{BASE_WEBHOOK_URL}")


def main() -> None:
    """Inialised dispatcher and webhook"""
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
    logger.info(f"WEBHOOK_URL--{BASE_WEBHOOK_URL}")
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exams Bot stopped!")
