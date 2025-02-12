import os
from dotenv import load_dotenv, find_dotenv

# Explicitly specify the path to the .env file
dotenv_path = find_dotenv(".env")
load_dotenv(dotenv_path)
print(dotenv_path)

# Get the bot token from environment variables
TOKEN = os.getenv("BOT_TOKEN")

if TOKEN:
    TOKEN = TOKEN.strip()
    space_dict = {index: char.isspace() for index, char in enumerate(TOKEN)}
    print(space_dict)
else:
    print("BOT_TOKEN environment variable is not set.")
