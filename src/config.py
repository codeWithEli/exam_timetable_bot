import os
from dotenv import load_dotenv
from enum import StrEnum

# load environment variables
load_dotenv()


class AppConfig(StrEnum):
    """Holds all application configuration variables"""

    TOKEN = os.environ.get("BOT_TOKEN")
    UG_URL = os.environ.get("UG_URL")
    BASE_WEBHOOK_URL = os.environ.get("WEBHOOK")
    WEB_SERVER_HOST = "0.0.0.0"
    WEB_SERVER_PORT = os.environ.get("PORT")
    DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID")
    CHROME_PATH = "/opt/google/chrome/chrome"
    CHROME_DRIVER_PATH = "/usr/bin/chromedriver"
    FIREBASE_CREDENTIALS_PATH = "./serviceAccount.json"
    FIREBASE_STORAGE_BUCKET = "ug-exams-bot.appspot.com"
