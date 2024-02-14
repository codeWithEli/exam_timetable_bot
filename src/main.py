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


if __name__ == "__main__":
    bot.infinity_polling()
    logger.info('Bot is running...')
