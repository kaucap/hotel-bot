from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp
from loguru import logger

from loader import dp


@logger.catch()
@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    logger.info(f'Клиент с id: {message.from_user.id} воспользовался командой /help')
    text = [
        'Список комманд',
        '/start - Запустить бота 💻',
        '/help - Помощь 📣',
        '/lowprice - Поиск самых дешёвых отелей в городе 📉',
        '/highprice - Поиск самых дорогих отелей в городе 📈',
        '/bestdeal - Поиск отелей, наиболее подходящих по цене и расположению от центра 🔥',
        '/rating - Поиск отелей, с самым высоким рейтингом 🔝',
        '/history - вывод истории поиска отелей 📖',
        '/clear - Очистить историю отелей 🚮'
    ]

    await message.answer('\n'.join(text))
