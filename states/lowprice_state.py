from aiogram.dispatcher.filters.state import StatesGroup, State


class LowPrice(StatesGroup):
    start = State()
    city = State()
    date_of_entry = State()
    departure_date = State()
    quantity_hotels = State()
    photo = State()
    result_without_photo = State()
    quantity_photo = State()
