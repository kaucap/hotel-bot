from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота 💻"),
        types.BotCommand("help", "Помощь 📣"),
        types.BotCommand("lowprice", "вывод самых дешёвых отелей в городе 📉"),
        types.BotCommand("highprice", "вывод самых дорогих отелей в городе 📈"),
        types.BotCommand("bestdeal", "вывод отелей, наиболее подходящих по цене и расположению от центра 🔥"),
        types.BotCommand("rating", 'вывод отелей, с самым высоким рейтингом 🔝'),
        types.BotCommand("history", "вывод истории поиска отелей 📖"),
        types.BotCommand("clear", 'очистить историю отелей 🚮')
    ])
