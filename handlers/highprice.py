from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from aiogram_calendar import dialog_cal_callback
from loguru import logger

from hotel_requests import get_hotel_info_expensive
from loader import dp
from states import HighPrice
from utils.common import get_entry_date, get_departure_date, ask_about_hotel_quantity, \
    send_results_without_photo, check_entered_city, send_results_with_photo


@logger.catch()
@dp.message_handler(Command("highprice"))
async def choose_city(message: types.Message):
    logger.info(f'Клиент с id: {message.from_user.id} запустил команду /highprice')
    await message.answer('Введите город')
    await HighPrice.city.set()


@logger.catch()
@dp.message_handler(state=HighPrice.city)
async def date_of_entry(message: types.Message, state: FSMContext):
    answer = message.text
    city_information = {'answer': answer, 'state': state, 'message': message, 'current_state': HighPrice}
    await check_entered_city(city_information=city_information)


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=HighPrice.date_of_entry)
async def date_of_entry_finish(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    entry_date_info = {'callback_query': callback_query, 'callback_data': callback_data, 'state': state,
                       'current_state': HighPrice}
    await get_entry_date(entry_date_info=entry_date_info)


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=HighPrice.departure_date)
async def departure_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    departure_date_info = {'callback_query': callback_query, 'callback_data': callback_data, 'state': state,
                           'current_state': HighPrice}
    await get_departure_date(departure_date_info=departure_date_info)


@logger.catch()
@dp.message_handler(state=HighPrice.quantity_hotels)
async def if_need_photo(message: types.Message, state: FSMContext):
    await ask_about_hotel_quantity(message=message, state=state, current_state=HighPrice)


@logger.catch()
@dp.message_handler(state=HighPrice.photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if 'Нет' in answer:
        search_information = {'message': message, 'state': state, 'find_hotel_func_name': get_hotel_info_expensive,
                              'current_state': 'highprice'}
        await send_results_without_photo(search_information=search_information)
    elif 'Да' in answer:
        await state.update_data(photo_need=answer)
        await message.answer('Какое количество фотографии показать?', reply_markup=ReplyKeyboardRemove())
        await HighPrice.quantity_photo.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nВведите "Да" или "Нет"')
        await HighPrice.photo.set()


@logger.catch()
@dp.message_handler(state=HighPrice.quantity_photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if answer.isdigit() is False:
        await message.answer('Ошибка ввода! ⛔ \nВведите число')
        await HighPrice.quantity_photo.set()
    elif answer == '0':
        await message.answer('Число должно быть больше нуля, попробуйте снова')
        await HighPrice.quantity_photo.set()
    else:
        search_information = {'state': state, 'message': message, 'answer': answer, 'current_state': 'highprice',
                              'find_hotel_func_name': get_hotel_info_expensive}
        await send_results_with_photo(search_information)
