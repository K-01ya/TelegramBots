# Telegram Bot
To start bot on your server:
- create bot with [@BotFather](https://t.me/BotFather), export bot tocken as `BOT_TOKEN` enviroment variable
- get personal key for [API](https://kinopoiskapiunofficial.tech/), export key as `X_API_KEY`
- start bot with  `BOT_TOKEN=your_tocken X_API_KEY=your_key python3 cinema_bot.py`

The bot has commands `start`, `help`, `stats`, `history`. To implement the last two
a small database was used, which is processed using `sqlite3`.
