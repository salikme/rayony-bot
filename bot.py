# -*- coding: utf-8 -*-
"""Telegram-бот «Районы и магазины» (aiogram 3) — чистая быстрая версия без ИИ."""
import asyncio
import json
import logging
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (BotCommand, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from engine import Game

BASE = Path(__file__).resolve().parent
SAVES = Path(os.getenv("SAVES_DIR") or BASE / "saves")
SAVES.mkdir(parents=True, exist_ok=True)

games: dict[int, Game] = {}
locks: dict[int, asyncio.Lock] = {}
dp = Dispatcher()
db = None  # пул asyncpg, если задана база данных


def read_setting(env: str, filename: str) -> str:
    """Берёт настройку из переменной окружения, а если её нет — из файла рядом с bot.py."""
    val = os.getenv(env, "").strip()
    if not val:
        f = BASE / filename
        if f.exists():
            val = f.read_text(encoding="utf-8").strip()
    return val


def clean_dsn(dsn: str) -> str:
    # asyncpg не понимает параметр channel_binding, который Neon добавляет в строку подключения
    parts = urlsplit(dsn)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunsplit(parts._replace(query=urlencode(query)))


async def init_db() -> None:
    global db
    dsn = read_setting("DATABASE_URL", "database_url.txt")
    if not dsn:
        logging.info("База не задана — сохранения пишутся в папку %s", SAVES)
        return
    import asyncpg
    db = await asyncpg.create_pool(clean_dsn(dsn), min_size=1, max_size=3)
    await db.execute(
        "CREATE TABLE IF NOT EXISTS saves (uid BIGINT PRIMARY KEY, data TEXT NOT NULL,"
        " updated TIMESTAMPTZ NOT NULL DEFAULT now())")
    logging.info("Сохранения хранятся в базе данных")


def save_path(uid: int) -> Path:
    return SAVES / f"{uid}.json"


async def has_save(uid: int) -> bool:
    if uid in games:
        return True
    if db is not None and await db.fetchval("SELECT 1 FROM saves WHERE uid=$1", uid):
        return True
    return save_path(uid).exists()


async def load_game(uid: int) -> Game:
    if uid in games:
        return games[uid]
    raw = None
    if db is not None:
        raw = await db.fetchval("SELECT data FROM saves WHERE uid=$1", uid)
    p = save_path(uid)
    if raw is None and p.exists():  # старое сохранение из файла
        raw = p.read_text(encoding="utf-8")
    g = None
    if raw is not None:
        try:
            g = Game(json.loads(raw))
        except Exception:
            logging.exception("Сохранение %s повреждено, начинаем заново", uid)
    if g is None:
        g = Game()
    games[uid] = g
    return g


async def save_game(uid: int, g: Game) -> None:
    data = json.dumps(g.to_dict(), ensure_ascii=False)
    if db is not None:
        await db.execute(
            "INSERT INTO saves (uid, data) VALUES ($1, $2) ON CONFLICT (uid)"
            " DO UPDATE SET data=EXCLUDED.data, updated=now()", uid, data)
        return
    p = save_path(uid)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(p)


def lock_for(uid: int) -> asyncio.Lock:
    if uid not in locks:
        locks[uid] = asyncio.Lock()
    return locks[uid]


def keyboard(g: Game, labels: list[str]) -> InlineKeyboardMarkup:
    turn = g.s["turn"]
    rows = [[InlineKeyboardButton(text=lbl, callback_data=f"c:{turn}:{i}")]
            for i, lbl in enumerate(labels)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_view(g: Game) -> tuple[str, InlineKeyboardMarkup]:
    text, labels = g.view()
    return text, keyboard(g, labels)


async def send_view(message: Message, g: Game) -> None:
    text, kb = render_view(g)
    await message.answer(text, reply_markup=kb)


async def edit_view(cq: CallbackQuery, g: Game) -> None:
    text, kb = render_view(g)
    try:
        await cq.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        await cq.message.answer(text, reply_markup=kb)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    uid = message.from_user.id
    async with lock_for(uid):
        fresh = not await has_save(uid)
        g = await load_game(uid)
        if fresh:
            await message.answer(
                "🏚 <b>«РАЙОНЫ И МАГАЗИНЫ»</b>\n"
                "Текстовый симулятор жизни на районе.\n\n"
                "Жми кнопки под сообщениями! /new — начать заново, /help — подсказки.")
        await save_game(uid, g)
        await send_view(message, g)


@dp.message(Command("new"))
async def cmd_new(message: Message):
    uid = message.from_user.id
    async with lock_for(uid):
        g = Game()
        games[uid] = g
        await save_game(uid, g)
        await message.answer("🔄 Новая игра.")
        await send_view(message, g)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    uid = message.from_user.id
    async with lock_for(uid):
        g = await load_game(uid)
        if not g.s["over"] and not g.s.get("fight"):
            g.help()
        await send_view(message, g)


@dp.callback_query(F.data.startswith("c:"))
async def on_choice(cq: CallbackQuery):
    uid = cq.from_user.id
    async with lock_for(uid):
        g = await load_game(uid)
        try:
            _, turn, idx = cq.data.split(":")
            turn, idx = int(turn), int(idx)
        except ValueError:
            await cq.answer()
            return
        if turn != g.s["turn"]:
            await cq.answer("Эта кнопка устарела — вот где ты сейчас.")
            await edit_view(cq, g)
            return
        try:
            g.choose(idx)
        except Exception:
            logging.exception("Ошибка в игре у %s", uid)
            g.sc = None
            g.buf = []
        await save_game(uid, g)
        await cq.answer()
        await edit_view(cq, g)


@dp.message(F.text)
async def any_text(message: Message):
    # В этой версии текст в чат просто игнорируется, вся игра идет по кнопкам — зато работает мгновенно
    uid = message.from_user.id
    async with lock_for(uid):
        g = await load_game(uid)
        await message.answer("ℹ️ Сейчас ИИ-диалоги отключены для скорости. Пользуйся кнопками под сообщениями!")
        await send_view(message, g)


def read_token() -> str:
    tok = read_setting("BOT_TOKEN", "token.txt")
    if not tok:
        raise SystemExit("Нет токена. Положите его в token.txt рядом с bot.py")
    return tok


async def start_health_server() -> None:
    """Маленькая веб-страница для хостингов вроде Render: они требуют открытый порт,
    а внешний пинг этой страницы не даёт бесплатному сервису заснуть."""
    port = os.getenv("PORT")
    if not port:
        return
    from aiohttp import web

    async def ok(_request):
        return web.Response(text="ok")

    app = web.Application()
    app.router.add_get("/", ok)
    app.router.add_get("/health", ok)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(port)).start()
    logging.info("Health-страница слушает порт %s", port)


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    await start_health_server()
    bot = Bot(read_token(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="Продолжить игру"),
        BotCommand(command="new", description="Начать заново"),
        BotCommand(command="help", description="Подсказки"),
    ])
    logging.info("Бот запущен в быстром режиме без ИИ")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())