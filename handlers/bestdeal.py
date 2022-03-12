import datetime
import re
from json import JSONDecodeError

from aiogram import types
from aiogram_calendar import DialogCalendar, dialog_cal_callback
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import MediaGroup, ReplyKeyboardRemove, CallbackQuery
from loguru import logger

from db_api import sql_commands as command
from hotel_requests import get_id_city, get_hotel_info_bestdeal, send_hotels_without_photo, set_hotels_with_photos
from keyboard.default import photo_hotel_necessity
from loader import dp
from states import BestDeal


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
    if re.search(r'\d', answer) is None:
        special_symbols = re.compile("|".join(map(re.escape, "@.,:;^№!?_*+()/#¤%&)"))).search
        if not bool(special_symbols(answer)):
            await state.update_data(city=answer)
            await message.answer('Введите диапазон цен в рублях за ночь через пробел, пример: 3000 5000')
            await BestDeal.price.set()
        else:
            await message.answer('Ошибка ввода! ⛔️ \nГород содержит спецсимволы, попробуйте снова')
            await BestDeal.city.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nГород содержит цифры, попробуйте снова')
        await BestDeal.city.set()


@logger.catch()
@dp.message_handler(state=BestDeal.price)
async def choose_distance(message: types.Message, state: FSMContext):
    answer = message.text
    list_of_prices = answer.split()
    if len(list_of_prices) == 2:
        if list_of_prices[0].isdigit() and list_of_prices[1].isdigit():
            start_price = int(list_of_prices[0])
            finish_price = int(list_of_prices[1])
            if start_price > finish_price:
                await message.answer('Ошибка ввода! ⛔ \nСтартовая цена не может быть больше конечной, '
                                     'попробуйте снова')
                await BestDeal.price
            elif start_price == finish_price:
                await message.answer('Ошибка ввода! ⛔ \nВведенные цены не могут быть одинаковыми, '
                                     'попробуйте снова')
            else:
                await state.update_data(start_price=start_price)
                await state.update_data(finish_price=finish_price)
                await message.answer('Введите диапазон расстояния отеля от центра города в км, пример: 0.3 1.5')
                await BestDeal.distance.set()
        else:
            await message.answer('Ошибка ввода! ⛔ \nВводить можно только цифры, попробуйте снова')
            await BestDeal.price.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nНужно ввести два значения, попробуйте снова')
        await BestDeal.price.set()


@logger.catch()
@dp.message_handler(state=BestDeal.distance)
async def choose_date(message: types.Message, state: FSMContext):
    answer = message.text
    list_of_distances = answer.split()
    if len(list_of_distances) == 2:
        start_distance = list_of_distances[0]
        finish_distance = list_of_distances[1]
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
    else:
        await message.answer('Ошибка ввода! ⛔ \nНужно ввести два значения, попробуйте снова')
        await BestDeal.distance.set()


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=BestDeal.date_of_entry)
async def date_of_entry_finish(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Дата въезда {date.strftime("%d/%m/%Y")}'
        )
        await state.update_data(date_of_entry=datetime.datetime.strptime(date.strftime("%Y%m%d"), "%Y%m%d").date())
        await callback_query.message.answer("Пожалуйста выберите дату выезда",
                                            reply_markup=await DialogCalendar().start_calendar())
        await BestDeal.departure_date.set()


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=BestDeal.departure_date)
async def departure_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Дата выезда {date.strftime("%d/%m/%Y")}'
        )
        await state.update_data(departure_date=datetime.datetime.strptime(date.strftime("%Y%m%d"), "%Y%m%d").date())

        await callback_query.message.answer('Введите количество отелей, которое нужно '
                                            'показать (максимальное количество: 25)')
        await BestDeal.quantity_hotels.set()


@logger.catch()
@dp.message_handler(state=BestDeal.quantity_hotels)
async def if_need_photo(message: types.Message, state: FSMContext):
    answer = message.text
    if re.search(r'\D', answer):
        await message.answer('Ошибка ввода! ⛔ \nМожно вводить только цифры, попробуйте снова')
        await BestDeal.quantity_hotels.set()
    elif 1 <= int(answer) <= 25:
        await state.update_data(quantity_hotels=answer)
        await message.answer('Нужно ли показать фото отелей?', reply_markup=photo_hotel_necessity)
        await BestDeal.photo.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nНужно ввести число от 1 до 25, попробуйте снова')
        await BestDeal.quantity_hotels.set()


@logger.catch()
@dp.message_handler(state=BestDeal.photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if 'Нет' in answer:
        await message.answer('Хорошо, приступаю к поиску 🔎', reply_markup=ReplyKeyboardRemove())
        logger.info("Бот приступает к выполнению команды /bestdeal")
        try:
            data = await state.get_data()
            days_quantity = (data['departure_date'] - data['date_of_entry']).days
            city_id = await get_id_city(data)
            hotels_information = await get_hotel_info_bestdeal(data, city_id)

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
        except JSONDecodeError:
            logger.error("Ошибка JSONDecodeError")
            await message.answer('Не получилось найти данные по введенному городу, попробуйте снова.\n'
                                 'Для этого пропишите команду /lowprice')
            await state.reset_state()
        except TypeError:
            logger.error("Ошибка TypeError")
            await message.answer('В ходе поиска возникла ошибка, попробуйте снова.\n'
                                 'Для этого пропишите команду /lowprice')
            await state.reset_state()
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
        await state.update_data(photo_quantity=answer)
        await message.answer('Хорошо, приступаю к поиску 🔎')
        logger.info("Бот приступает к выполнению команды /bestdeal")
        try:
            data = await state.get_data()
            days_quantity = (data['departure_date'] - data['date_of_entry']).days
            city_id = await get_id_city(data)
            hotels_information = await get_hotel_info_bestdeal(data, city_id)
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
        except JSONDecodeError:
            logger.error("Ошибка JSONDecodeError")
            await message.answer('Не получилось найти данные по введенному городу, попробуйте снова.\n'
                                 'Для этого пропишите команду /bestdeal')
            await state.reset_state()
        except TypeError:
            logger.error("Ошибка TypeError")
            await message.answer('В ходе поиска возникла ошибка, попробуйте снова.\n'
                                 'Для этого пропишите команду /bestdeal')
            await state.reset_state()
