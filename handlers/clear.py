from aiogram import types
from aiogram.dispatcher.filters import Command
from loguru import logger

from db_api.schemas.hotel import Hotel
from db_api.schemas.user import User
from loader import dp


@logger.catch()
@dp.message_handler(Command("clear"))
async def clear_hotel_history(message: types.Message):
    logger.info(f'Клиент с id: {message.from_user.id} очистил историю отелей')
    user = await User.get(message.from_user.id)
    await Hotel.delete.where(user.id == Hotel.id).gino.status()
    await message.answer('История отелей удалена 🚮')
