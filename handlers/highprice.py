import datetime
import re
from json import JSONDecodeError

from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import MediaGroup, ReplyKeyboardRemove, CallbackQuery
from loguru import logger
from aiogram_calendar import DialogCalendar, dialog_cal_callback

from db_api import sql_commands as command
from hotel_requests import get_id_city, get_hotel_info_expensive, send_hotels_without_photo, set_hotels_with_photos
from keyboard.default import photo_hotel_necessity
from loader import dp
from states import HighPrice


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
    if re.search(r'\d', answer) is None:
        special_symbols = re.compile("|".join(map(re.escape, "@.,:;^№!?_*+()/#¤%&)"))).search
        if not bool(special_symbols(answer)):
            await state.update_data(city=answer)
            await message.answer("Пожалуйста выберите дату въезда",
                                 reply_markup=await DialogCalendar().start_calendar())
            await HighPrice.date_of_entry.set()
        else:
            await message.answer('Ошибка ввода! ⛔️ \nГород содержит спецсимволы, попробуйте снова')
            await HighPrice.city.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nГород содержит цифры, попробуйте снова')
        await HighPrice.city.set()


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=HighPrice.date_of_entry)
async def date_of_entry_finish(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Дата въезда {date.strftime("%d/%m/%Y")}'
        )
        await state.update_data(date_of_entry=datetime.datetime.strptime(date.strftime("%Y%m%d"), "%Y%m%d").date())
        await callback_query.message.answer("Пожалуйста выберите дату выезда",
                                            reply_markup=await DialogCalendar().start_calendar())
        await HighPrice.departure_date.set()


@logger.catch()
@dp.callback_query_handler(dialog_cal_callback.filter(), state=HighPrice.departure_date)
async def departure_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'Дата выезда {date.strftime("%d/%m/%Y")}'
        )
        await state.update_data(departure_date=datetime.datetime.strptime(date.strftime("%Y%m%d"), "%Y%m%d").date())

        await callback_query.message.answer('Введите количество отелей, которое нужно '
                                            'показать (максимальное количество: 25)')
        await HighPrice.quantity_hotels.set()


@logger.catch()
@dp.message_handler(state=HighPrice.quantity_hotels)
async def if_need_photo(message: types.Message, state: FSMContext):
    answer = message.text
    if re.search(r'\D', answer):
        await message.answer('Ошибка ввода! ⛔ \nМожно вводить только цифры')
        await HighPrice.quantity_hotels.set()
    elif 1 <= int(answer) <= 25:
        await state.update_data(quantity_hotels=answer)
        await message.answer('Нужно ли показать фото отелей?', reply_markup=photo_hotel_necessity)
        await HighPrice.photo.set()
    else:
        await message.answer('Ошибка ввода! ⛔ \nНужно ввести число от 1 до 25')
        await HighPrice.quantity_hotels.set()


@logger.catch()
@dp.message_handler(state=HighPrice.photo)
async def result(message: types.Message, state: FSMContext):
    answer = message.text
    if 'Нет' in answer:
        await message.answer('Хорошо, приступаю к поиску 🔎', reply_markup=ReplyKeyboardRemove())
        logger.info("Бот приступает к выполнению команды /highprice")
        try:
            data = await state.get_data()
            days_quantity = (data['departure_date'] - data['date_of_entry']).days
            city_id = await get_id_city(data)
            hotels_information = await get_hotel_info_expensive(data, city_id)

            for index in range(len(hotels_information)):
                await send_hotels_without_photo(hotels_information=hotels_information, index=index, command=command,
                                                days_quantity=days_quantity, message=message)

            await state.reset_state()
            await message.answer('Команда выполнена. Для просмотра всего функционала введите /help')
        except JSONDecodeError:
            logger.error("Ошибка JSONDecodeError")
            await message.answer('Не получилось найти данные по введенному городу, попробуйте снова.\n'
                                 'Для этого пропишите команду /highprice')
            await state.reset_state()
        except TypeError:
            logger.error("Ошибка TypeError")
            await message.answer('В ходе поиска возникла ошибка, попробуйте снова.\n'
                                 'Для этого пропишите команду /highprice')
            await state.reset_state()

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
        await state.update_data(photo_quantity=answer)
        await message.answer('Хорошо, приступаю к поиску 🔎')
        logger.info("Бот приступает к выполнению команды /highprice")
        try:
            data = await state.get_data()
            days_quantity = (data['departure_date'] - data['date_of_entry']).days
            city_id = await get_id_city(data)
            hotels_information = await get_hotel_info_expensive(data, city_id)

            for index in range(len(hotels_information)):
                await set_hotels_with_photos(MediaGroup=MediaGroup, command=command, data=data,
                                             days_quantity=days_quantity, hotels_information=hotels_information,
                                             index=index, message=message)

            await state.reset_state()
            await message.answer('Команда выполнена. Для просмотра всего функционала введите /help')
        except JSONDecodeError:
            logger.error("Ошибка JSONDecodeError")
            await message.answer('Не получилось найти данные по введенному городу, попробуйте снова.\n'
                                 'Для этого пропишите команду /highprice')
            await state.reset_state()
        except TypeError:
            logger.error("Ошибка TypeError")
            await message.answer('В ходе поиска возникла ошибка, попробуйте снова.\n'
                                 'Для этого пропишите команду /highprice')
            await state.reset_state()
