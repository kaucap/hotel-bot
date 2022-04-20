import re
from json import JSONDecodeError

from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import MediaGroup, ReplyKeyboardRemove
from aiogram_calendar import DialogCalendar
from loguru import logger

from db_api import sql_commands as command
from hotel_requests import get_id_city, get_hotel_info_bestdeal, send_hotels_without_photo, set_hotels_with_photos
from states import BestDeal
from utils.common import json_decode_error, type_error


async def check_special_symbols(symbol_information: dict):
    answer = symbol_information['answer']
    state = symbol_information['state']
    current_state = symbol_information['current_state']
    message = symbol_information['message']

    special_symbols = re.compile("|".join(map(re.escape, "@.,:;^№!?_*+()/#¤%&)"))).search
    if not bool(special_symbols(answer)):
        await state.update_data(city=answer)
        await message.answer('Введите диапазон цен в рублях за ночь через пробел, пример: 3000 5000')
        await current_state.price.set()
    else:
        await message.answer('Ошибка ввода! ⛔️ \nГород содержит спецсимволы, попробуйте снова')
        await current_state.city.set()


async def check_entered_city(city_information: dict):
    answer = city_information['answer']
    state = city_information['state']
    message = city_information['message']
    current_state = city_information['current_state']

    if re.search(r'\d', answer) is None:
        symbol_information = {'message': message, 'state': state, 'current_state': current_state, 'answer': answer}
        await check_special_symbols(symbol_information=symbol_information)
    else:
        await message.answer('Ошибка ввода! ⛔ \nГород содержит цифры, попробуйте снова')
        await current_state.city.set()


async def user_input_distance_from_center(acquired_information: dict):
    state = acquired_information['state']
    start_price = acquired_information['start_price']
    finish_price = acquired_information['finish_price']
    message = acquired_information['message']

    await state.update_data(start_price=start_price)
    await state.update_data(finish_price=finish_price)
    await message.answer('Введите диапазон расстояния отеля от центра города в км, пример: 0.3 1.5')
    await BestDeal.distance.set()


async def check_price_difference(price_information: dict):
    start_price = int(price_information['start_price'])
    finish_price = int(price_information['finish_price'])
    message = price_information['message']
    state = price_information['state']

    if start_price > finish_price:
        await message.answer('Ошибка ввода! ⛔ \nСтартовая цена не может быть больше конечной, '
                             'попробуйте снова')
        await BestDeal.price
    elif start_price == finish_price:
        await message.answer('Ошибка ввода! ⛔ \nВведенные цены не могут быть одинаковыми, '
                             'попробуйте снова')
    else:
        acquired_information = {'state': state, 'message': message, 'start_price': start_price,
                                'finish_price': finish_price}
        await user_input_distance_from_center(acquired_information)


async def check_entered_prices(price_information: dict):
    start_price = price_information['start_price']
    finish_price = price_information['finish_price']
    message = price_information['message']

    if start_price.isdigit() and finish_price.isdigit():
        await check_price_difference(price_information=price_information)
    else:
        await message.answer('Ошибка ввода! ⛔ \nВводить можно только цифры, попробуйте снова')
        await BestDeal.price.set()


async def check_entered_distances(distance_information: dict):
    start_distance = distance_information['start_distance']
    finish_distance = distance_information['finish_distance']
    message = distance_information['message']
    state = distance_information['state']

    if start_distance.isdigit() or finish_distance.isdigit() or re.findall(r"\d*\.\d+", start_distance) \
            or re.findall(r"\d*\.\d+", finish_distance):
        if start_distance > finish_distance:
            await message.answer('Ошибка ввода! ⛔ \nПервое число не может быть больше второго, '
                                 'попробуйте снова')
            await BestDeal.distance.set()
        else:
            await state.update_data(start_distance=start_distance)
            await state.update_data(finish_distance=finish_distance)
            await message.answer("Пожалуйста выберите дату въезда",
                                 reply_markup=await DialogCalendar().start_calendar())
            await BestDeal.date_of_entry.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nВведенные данные не являются числом, попробуйте снова')
        await BestDeal.distance.set()


async def check_if_have_hotels_without_photos(search_information: dict):
    hotels_information = search_information['hotels_information']
    message = search_information['message']
    state = search_information['state']
    days_quantity = search_information['days_quantity']

    if len(hotels_information) == 0:
        await message.answer('К сожалению по вашему запросу ничего не найдено. Попробуйте изменить '
                             'критерии поиска и попробовать снова. Для этого введите команду '
                             '/bestdeal')
        await state.reset_state()
    else:
        for index in range(len(hotels_information)):
            await send_hotels_without_photo(hotels_information=hotels_information, index=index, command=command,
                                            days_quantity=days_quantity, message=message)

        await state.reset_state()
        await message.answer('Команда выполнена. Для просмотра всего функционала введите /help')


async def send_info_to_user_without_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    days_quantity = (data['departure_date'] - data['date_of_entry']).days
    city_id = await get_id_city(data)
    hotels_information = await get_hotel_info_bestdeal(data, city_id)
    search_information = {'hotels_information': hotels_information, 'days_quantity': days_quantity,
                          'message': message, 'state': state}
    await check_if_have_hotels_without_photos(search_information=search_information)


async def send_results_without_photo(message: types.Message, state: FSMContext):
    await message.answer('Хорошо, приступаю к поиску 🔎', reply_markup=ReplyKeyboardRemove())
    logger.info("Бот приступает к выполнению команды /bestdeal")
    try:
        await send_info_to_user_without_photo(state=state, message=message)
    except JSONDecodeError:
        error_information = {'message': message, 'state': state, 'current_command': 'bestdeal'}
        await json_decode_error(error_information=error_information)
    except TypeError:
        error_information = {'message': message, 'state': state, 'current_command': 'bestdeal'}
        await type_error(error_information=error_information)


async def check_if_have_hotels_with_photos(search_information: dict):
    hotels_information = search_information['hotels_information']
    message = search_information['message']
    state = search_information['state']
    days_quantity = search_information['days_quantity']
    data = search_information['data']

    if len(hotels_information) == 0:
        await message.answer('К сожалению по вашему запросу ничего не найдено. Попробуйте изменить '
                             'критерии поиска и попробовать снова. Для этого введите команду '
                             '/bestdeal')
        await state.reset_state()
    else:
        for index in range(len(hotels_information)):
            await set_hotels_with_photos(MediaGroup=MediaGroup, command=command, data=data,
                                         days_quantity=days_quantity, hotels_information=hotels_information,
                                         index=index, message=message)

    await state.reset_state()
    await message.answer('Команда выполнена. Для просмотра всего функционала введите /help')


async def send_info_to_user_with_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    days_quantity = (data['departure_date'] - data['date_of_entry']).days
    city_id = await get_id_city(data)
    hotels_information = await get_hotel_info_bestdeal(data, city_id)
    search_information = {'hotels_information': hotels_information, 'days_quantity': days_quantity,
                          'message': message, 'state': state, 'data': data}
    await check_if_have_hotels_with_photos(search_information=search_information)


async def send_results_with_photo(message: types.Message, state: FSMContext, answer: str):
    await state.update_data(photo_quantity=answer)
    await message.answer('Хорошо, приступаю к поиску 🔎')
    logger.info("Бот приступает к выполнению команды /bestdeal")
    try:
        await send_info_to_user_with_photos(state=state, message=message)
    except JSONDecodeError:
        error_information = {'message': message, 'state': state, 'current_command': 'bestdeal'}
        await json_decode_error(error_information=error_information)
    except TypeError:
        error_information = {'message': message, 'state': state, 'current_command': 'bestdeal'}
        await type_error(error_information=error_information)
