import aiohttp
from googlesearch import search
import os

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import sqlite3
from pypika import Query, Table, functions


X_API_KEY = os.environ['X_API_KEY']
bot = Bot(token=os.environ['BOT_TOKEN'])
dp = Dispatcher(bot)


connection = sqlite3.connect("history.db")
cursor = connection.cursor()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    await bot.send_message(message.from_user.id, "Привет! \n"
                                                 "Это бот, который поможет искать фильмы по названию, "
                                                 "для большей информации воспользуйся /help")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message) -> None:
    await bot.send_message(message.from_user.id, "1. Чтобы получить информацию о фильме введи его название \n"
                                                 "2. Чтобы узнать историю запросов воспользуйся /history \n"
                                                 "3. Чтобы узнать статистику запросов воспользуйся /stats \n"
                           )


@dp.message_handler(commands=['history'])
async def history_command(message: types.Message) -> None:
    messages = Table('messages')

    q = Query.from_(messages).select("message", "film")
    q = q.where(messages.id == message.from_user.id)

    cursor.execute(str(q))
    requests_history = cursor.fetchall()

    ans = "История запросов:\n"
    for request in requests_history:
        ans += f"<b>{request[0]}</b>: {request[1]}\n"

    await bot.send_message(message.from_user.id, ans, parse_mode="HTML")


@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message) -> None:
    messages = Table('messages')

    q = Query.from_(messages)
    q = q.where(messages.id == message.from_user.id)
    q = q.groupby(messages.film).select(messages.film, functions.Count(messages.film))

    cursor.execute(str(q))
    requests_stat = cursor.fetchall()

    ans = "Статистика запросов:\n"
    for request in sorted(requests_stat, key=lambda x: x[1], reverse=True):
        ans += f"<b>{request[0]}</b>: {request[1]}\n"
    await bot.send_message(message.from_user.id, ans, parse_mode="HTML")


async def get_film_info(keyword: str) -> tuple[str, str, str] | None:
    async with aiohttp.ClientSession(headers={'X-API-KEY': X_API_KEY,
                                              'Content-Type': 'application/json'}) as session:
        url = "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"
        async with session.get(url, params={"keyword": keyword}) as resp:
            res = await resp.json()
            films = res["films"]
            if len(films) == 0:
                return None

            film_info = films[0]
            film_name = film_info['nameRu'] if "nameRu" in film_info else film_info['nameEn']
            description = ''.join(film_info['description'].split('\n\n')) if "description" in film_info \
                else "пока что нет описания"
            url_for_watching = next(iter(search(f"Смотреть онлайн бесплатно {film_name}", lang="ru", num_results=1)))

            ans = f"<b> {film_name}</b>, {film_info['year']}\n"
            ans += (f"<b>рейтинг </b>: {film_info['rating']}\n" if film_info['rating'] != "null"
                    else "<b>рейтинга пока что еще нет! </b>")
            ans += f"\n{description}\n"
            ans += f"<a href=\'{url_for_watching}\'>Ссылка для просмотра</a>\n"
            return ans, film_name, film_info['posterUrl']


@dp.message_handler()
async def common_reply(message: types.Message) -> None:
    response = await get_film_info(message.text)
    if response is not None:
        ans, film_name, image_url = response
        await bot.send_message(message.from_user.id, ans, parse_mode='HTML')
        await bot.send_photo(message.from_user.id, image_url)

        messages = Table('messages')
        q = Query.into(messages).insert(message.chat.id, message.text, film_name)
        cursor.execute(str(q))
        connection.commit()
    else:
        await bot.send_message(message.from_user.id, "Такого фильма, кажется, нет :(")


if __name__ == "__main__":
    cursor.execute("CREATE TABLE IF NOT EXISTS messages(id integer NOT NULL,"
                   " message text NOT NULL, film text NOT NULL)")
    connection.commit()
    executor.start_polling(dp)
    connection.close()
