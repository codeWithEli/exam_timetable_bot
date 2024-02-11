import os
import re
import logging
import dotenv
import scraper

import telegram.ext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configure logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

dotenv.load_dotenv()
PORT = int(os.environ.get("PORT", "8443"))
TOKEN = os.environ["TOKEN"]

scraper = scraper.Scraper()

state = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command."""
    keyboard = [
        [InlineKeyboardButton(
            "Exams schedule", callback_data='exams_schedule')],
        [InlineKeyboardButton("Exact exams venue",
                              callback_data='exact_venue')],
        [InlineKeyboardButton("All exams", callback_data='all_exams')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"""
Hello {update.message.from_user.username},
Welcome to the Exams Timetable Bot! 
This bot helps University of Ghana students 
find their exam venues with ease. 

Get your exam date, time, and venue instantly.
    """, reply_markup=reply_markup
    )


async def button(update, context):
    """Button command."""
    global state
    query = update.callback_query
    await query.answer()

    if query.data == 'exams_schedule':

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Please enter your course code (eg: ugrc101).")

    elif query.data == 'get_exact_venue':
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Please enter your id.")
        context.user_data['state'] = "waiting for id"


async def handle_course_code(update, context):
    """Handle course code command."""
    global state
    global course_code

    if context.user_data.get('state') == "waiting for id":
        return

    course_code = update.message.text

    course_name = course_code.split(" ")

    course_code_cleaned = course_code.replace(" ", "")

    if not course_name[0].isalpha():
        return

    # Check if the course code matches the format (4 letters and 3 numbers)
    if not re.match(r'^[A-Za-z]{4}\d{3}$',  course_code_cleaned):
        await update.message.reply_text(
            "Invalid course code. Please enter a course code with 4 letters followed by 3 numbers.")
        return

    await update.message.reply_text(f"Searching for {course_code_cleaned}...")

    screenshot_url = scraper.single_exams_schedule(course_code_cleaned)

    keyboard = [[InlineKeyboardButton(
        "Get Exact Venue", callback_data='get_exact_venue')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(photo=screenshot_url, reply_markup=reply_markup)

    context.user_data['state'] = "waiting for id"
    logger.info("State set to waiting for id")


async def handle_id(update, context):
    """Handle id command."""
    global state
    global course_code

    if context.user_data.get('state') == "waiting for id":
        logger.info("waiting for ID")
        id = int(update.message.text)

        await update.message.reply_text("Got ID. Finding venue...")

        result = await scraper.find_exact_exams_venue(course_code=course_code, ID=id)

        await update.message.reply_text(f"Here is your exam venue: {result}")

        context.user_data['state'] = None
    else:
        return


def main():
    """Start bot."""
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(telegram.ext.CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(button))

    app.add_handler(MessageHandler(filters.TEXT & (
        ~filters.COMMAND), handle_id))

    app.add_handler(MessageHandler(filters.TEXT & (
        ~filters.COMMAND), handle_course_code))

    # pollling
    app.run_polling()


if __name__ == "__main__":
    main()
