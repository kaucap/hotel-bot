from aiogram.dispatcher.filters.state import StatesGroup, State


class BestDeal(StatesGroup):
    start = State()
    city = State()
    price = State()
    distance = State()
    date_of_entry = State()
    departure_date = State()
    quantity_hotels = State()
    photo = State()
    result_without_photo = State()
    quantity_photo = State()
