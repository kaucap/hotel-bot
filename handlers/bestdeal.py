from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from aiogram_calendar import dialog_cal_callback
from loguru import logger

from loader import dp
from states import BestDeal
from utils.bestdeal import check_entered_prices, check_entered_distances, \
    send_results_without_photo, send_results_with_photo, check_entered_city
from utils.common import get_entry_date, get_departure_date, ask_about_hotel_quantity


@logger.catch()
@dp.message_handler(Command("bestdeal"))
async def choose_city(message: types.Message):
    logger.info(f'Клиент с id: {message.from_user.id} запустил команду /bestdeal')
    await message.answer('Введите город')
    await BestDeal.city.set()


@logger.catch()
@dp.message_handler(state=BestDeal.city)
async def choose_price(message: types.Message, state: FSMContext):
    answer = message.text
    city_information = {'answer': answer, 'state': state, 'message': message, 'current_state': BestDeal}
    await check_entered_city(city_information=city_information)


@logger.catch()
@dp.message_handler(state=BestDeal.price)
async def choose_distance(message: types.Message, state: FSMContext):
    answer = message.text
    list_of_prices = answer.split()
    if len(list_of_prices) == 2:
        price_information = {'start_price': list_of_prices[0], 'finish_price': list_of_prices[1],
                             'message': message, 'state': state}
        await check_entered_prices(price_information)
    else:
        await message.answer('Ошибка ввода! ⛔ \nНужно ввести два значения, попробуйте снова')
        await BestDeal.price.set()


@logger.catch()
@dp.message_handler(state=BestDeal.distance)
async def choose_date(message: types.Message, state: FSMContext):
    answer = message.text
    list_of_distances = answer.split()
    if len(list_of_distances) == 2:
        distance_information = {'start_distance': list_of_distances[0], 'finish_distance': list_of_distances[1],
                                'message': message, 'state': state}
        await check_entered_distances(distance_information)
    else:
        await message.answer('Ошибка ввода! ⛔ \nНужно ввести два значения, попробуйте снова')
        await BestDeal.distance.set()


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=BestDeal.date_of_entry)
async def date_of_entry_finish(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    entry_date_info = {'callback_query': callback_query, 'callback_data': callback_data, 'state': state,
                       'current_state': BestDeal}
    await get_entry_date(entry_date_info=entry_date_info)


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=BestDeal.departure_date)
async def departure_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    departure_date_info = {'callback_query': callback_query, 'callback_data': callback_data, 'state': state,
                           'current_state': BestDeal}
    await get_departure_date(departure_date_info=departure_date_info)


@logger.catch()
@dp.message_handler(state=BestDeal.quantity_hotels)
async def if_need_photo(message: types.Message, state: FSMContext):
    await ask_about_hotel_quantity(message=message, state=state, current_state=BestDeal)


@logger.catch()
@dp.message_handler(state=BestDeal.photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if 'Нет' in answer:
        await send_results_without_photo(message=message, state=state)
    elif 'Да' in answer:
        await state.update_data(photo_need=answer)
        await message.answer('Какое количество фотографии показать?', reply_markup=ReplyKeyboardRemove())
        await BestDeal.quantity_photo.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nВведите "Да" или "Нет"')
        await BestDeal.photo.set()


@logger.catch()
@dp.message_handler(state=BestDeal.quantity_photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if answer.isdigit() is False:
        await message.answer('Ошибка ввода! ⛔ \nВведите число')
        await BestDeal.quantity_photo.set()
    elif answer == '0':
        await message.answer('Число должно быть больше нуля, попробуйте снова')
        await BestDeal.quantity_photo.set()
    else:
        await send_results_with_photo(message=message, state=state, answer=answer)
