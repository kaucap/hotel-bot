from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from loguru import logger

from db_api import sql_commands as command
from loader import dp


@logger.catch()
@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    name = message.from_user.full_name
    await command.add_user(id=message.from_user.id, name=name)
    logger.info(f'Клиент с id: {message.from_user.id} запустил бота')
    text = 'Приветствую! 👋 \nЧтобы узнать функционал бота, пропишите комманду /help'
    await message.answer(text)
