from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

photo_hotel_necessity = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Да ✅'),
            KeyboardButton(text='Нет ❌')
        ]
    ],
    resize_keyboard=True
)
