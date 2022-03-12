from loguru import logger

from bot_commands import set_default_commands
from db_api import db_gino
from db_api.db_gino import db

logger.add("debug.log", format="{time} {level} {message}", level="DEBUG", rotation="1 week",
           compression="zip")


@logger.catch()
async def on_startup(dp):
    await set_default_commands(dp)

    logger.info('Подключаем БД')
    await db_gino.on_startup(dp)

    logger.info('Чистим базу')
    await db.gino.drop_all()

    logger.info('Создаем таблицы')
    await db.gino.create_all()


if __name__ == '__main__':
    from aiogram import executor
    from handlers import dp

    executor.start_polling(dp, on_startup=on_startup)
