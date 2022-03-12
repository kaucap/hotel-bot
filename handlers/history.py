from aiogram import types
from aiogram.dispatcher.filters import Command
from loguru import logger

from db_api import sql_commands as command
from db_api.schemas.user import User
from loader import dp


@logger.catch()
@dp.message_handler(Command("history"))
async def show_hotel_history(message: types.Message):
    user = await User.get(message.from_user.id)
    hotels = await command.choose_hotels(user.id)
    logger.info(f'Клиент с id: {message.from_user.id} запросил историю отелей')
    if len(hotels) > 0:
        for hotel in hotels:
            await message.answer(f'Название отеля {hotel.name}\n'
                                 f'Адрес: {hotel.address}\nРасстояие до центра города: {hotel.distance} км'
                                 f'\nЦена за ночь: {hotel.night_price} рублей\n'
                                 f'Цена за весь период: {hotel.all_period_price} рублей\n')
    else:
        await message.answer('История отелей пуста')
