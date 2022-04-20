from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from aiogram_calendar import dialog_cal_callback
from loguru import logger

from hotel_requests import get_hotel_info_by_rating
from loader import dp
from states import Rating
from utils.common import check_entered_city, get_entry_date, get_departure_date, send_results_without_photo, \
    send_results_with_photo, ask_about_hotel_quantity


@logger.catch()
@dp.message_handler(Command("rating"))
async def choose_city(message: types.Message):
    logger.info(f'Клиент с id: {message.from_user.id} запустил команду /rating')
    await message.answer('Введите город')
    await Rating.city.set()


@logger.catch()
@dp.message_handler(state=Rating.city)
async def choose_dates(message: types.Message, state: FSMContext):
    answer = message.text
    city_information = {'answer': answer, 'state': state, 'message': message, 'current_state': Rating}
    await check_entered_city(city_information=city_information)


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=Rating.date_of_entry)
async def date_of_entry_finish(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    entry_date_info = {'callback_query': callback_query, 'callback_data': callback_data, 'state': state,
                       'current_state': Rating}
    await get_entry_date(entry_date_info=entry_date_info)


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=Rating.departure_date)
async def departure_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    departure_date_info = {'callback_query': callback_query, 'callback_data': callback_data, 'state': state,
                           'current_state': Rating}
    await get_departure_date(departure_date_info=departure_date_info)


@logger.catch()
@dp.message_handler(state=Rating.quantity_hotels)
async def if_need_photo(message: types.Message, state: FSMContext):
    await ask_about_hotel_quantity(message=message, state=state, current_state=Rating)


@logger.catch()
@dp.message_handler(state=Rating.photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if 'Нет' in answer:
        search_information = {'message': message, 'state': state, 'find_hotel_func_name': get_hotel_info_by_rating,
                              'current_state': 'rating'}
        await send_results_without_photo(search_information=search_information)
    elif 'Да' in answer:
        await state.update_data(photo_need=answer)
        await message.answer('Какое количество фотографии показать?', reply_markup=ReplyKeyboardRemove())
        await Rating.quantity_photo.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nВведите "Да" или "Нет"')
        await Rating.photo.set()


@logger.catch()
@dp.message_handler(state=Rating.quantity_photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if answer.isdigit() is False:
        await message.answer('Ошибка ввода! ⛔ \nВведите число')
        await Rating.quantity_photo.set()
    elif answer == '0':
        await message.answer('Число должно быть больше нуля, попробуйте снова')
        await Rating.quantity_photo.set()
    else:
        search_information = {'state': state, 'message': message, 'answer': answer, 'current_state': 'rating',
                              'find_hotel_func_name': get_hotel_info_by_rating}
        await send_results_with_photo(search_information)
