import json
import logging
import asyncio
import aioschedule
import random
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.filters.builtin import ChatTypeFilter
from aiogram import types
from aiogram.dispatcher import FSMContext
from modules.database_orm import *
from aiogram.utils import executor
from aiogram.dispatcher.filters import *
import datetime as dt
import time


FINE = 2
TIME_OUT_MESSAGE = 3000

class User_Active:

    def __init__(self, user_id):
        self.user_id = user_id
        self.bonus = 25
        self.time = time.time()


    async def noflud(self):

        if (time.time() - self.time) * 1000 < TIME_OUT_MESSAGE:
            return False
        self.bonus += 25
        self.time = time.time()
        return True




# Logging
formater_logging_message = logging.Formatter("------------------------\n\nTime: %(asctime)s\nLevel: %(levelname)s\nMessage: %(message)s\n")
file_log = logging.FileHandler("logs/logs.txt")
console_log = logging.StreamHandler()
file_log.setFormatter(formater_logging_message)
console_log.setFormatter(formater_logging_message)
logging.basicConfig(level=logging.INFO, handlers=(file_log, console_log), encoding="utf-8")


# Variable env path
VARIABLE_ENV_PATH = "config/variable_env.json"


# Client text path
CLIENT_TEXT_PATH = "static/clent_text.json"


PRICE_BUYBACK = 200
FINE_BAKA = 200
BONUS = 300

EVENT_TIME_MAIN = "09:00"

# Get client text from JSON File
with open(CLIENT_TEXT_PATH, "r", encoding="utf-8") as file_data:
    client_text = json.loads(file_data.read())
    file_data.close()


# Get variable env data
with open(VARIABLE_ENV_PATH, "r", encoding="utf-8") as file_data:
    variable = json.loads(file_data.read())
    file_data.close()


# Storage
storage = MemoryStorage()


# Initialize Bot
bot = Bot(token=variable["BOT_TOKEN"])


# Initialize Dispatcher
dp = Dispatcher(bot, storage=storage)

# TELEGRAM ID BOT
# BOT_ID = await bot.get_me()

users_activity = {}

users_buyback = {}



# Create or open database
with db:
    db.create_tables([User])