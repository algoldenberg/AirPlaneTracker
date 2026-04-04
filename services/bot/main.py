import os
import logging
import asyncio
import aiohttp
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bot")

TOKEN         = os.getenv("TELEGRAM_TOKEN")
API_URL       = os.getenv("API_URL", "http://api:8000")
DB_PATH       = os.getenv("DB_PATH", "/data/flights.db")
POLL_INTERVAL = 10
OREF_INTERVAL = 5

TARGET_AREAS = [
    "תל אביב - דרום",
    "תל אביב - מרכז העיר",
    "תל אביב - מזרח",
    "תל אביב - יפו",
    "תל אביב - דרום העיר ויפו",
]

AREA_TRANSLATIONS = {
    "תל אביב - דרום":           "Tel Aviv - South",
    "תל אביב - מרכז העיר":      "Tel Aviv - City Center",
    "תל אביב - מזרח":           "Tel Aviv - East",
    "תל אביב - יפו":            "Tel Aviv - Jaffa",
    "תל אביב - דרום העיר ויפו": "Tel Aviv - South & Jaffa",
}

TITLE_TRANSLATIONS = {
    "ירי רקטות וטילים":     "Rocket & Missile Fire",
    "חדירת כלי טיס עוין":   "Hostile Aircraft Intrusion",
    "רעידת אדמה":           "Earthquake",
    "חשד לחדירת מחבלים":    "Suspected Terrorist Infiltration",
    "אירוע חומרים מסוכנים": "Hazardous Materials Incident",
    "התרעה בשל גל צונמי":   "Tsunami Warning",
    "בדקות הקרובות צפויות להתקבל התרעות באזורך": "Alerts expected in your area soon",
    "האירוע הסתיים":         "Event Ended",
}

# cat=10 или cat=13 — event ended
# cat=14 — pre-alert
# cat=1 и остальные — основная сирена
CAT_ENDED    = {"10", "13"}
CAT_PREALERT = {"14"}

LOGO_ALERT    = "/app/RedAlertLogo.png"
LOGO_PREALERT = "/app/HereWeGoAgain.png"
LOGO_ENDED    = "/app/Spitz.png"

bot = Bot(token=TOKEN)
dp  = Dispatcher()

notified: set[str] = set()
alerted:  set[str] = set()


# ── Subscribers в SQLite ─────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    return conn


def load_subscribers() -> set[int]:
    conn = get_db()
    try:
        rows = conn.execute("SELECT chat_id FROM subscribers").fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def save_subscriber(chat_id: int):
    conn = get_db()
    try:
        conn.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
    finally:
        conn.close()


subscribers: set[int] = load_subscribers()


# ── Helpers ──────────────────────────────────────────────────────────────────

def format_flight(f: dict) -> str:
    origin      = f.get("origin") or "???"
    destination = f.get("destination") or "???"
    callsign    = f.get("callsign") or "—"
    aircraft    = f.get("aircraft") or "—"
    alt         = f.get("altitude_ft")
    spd         = f.get("speed_kts")
    hdg         = f.get("heading_deg")
    alt_str     = f"{alt:,} ft" if alt else "—"
    spd_str     = f"{spd} kts" if spd else "—"
    hdg_str     = f"{hdg}°" if hdg else "—"
    return (
        f"✈ *{callsign}* — {aircraft}\n"
        f"🛫 {origin} → {destination}\n"
        f"📐 {alt_str} | {spd_str} | {hdg_str}"
    )


def format_time(updated_at: str) -> str:
    try:
        dt = datetime.fromisoformat(updated_at)
        return dt.astimezone(ZoneInfo("Asia/Jerusalem")).strftime("%H:%M")
    except:
        return "—"


def history_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 История за 24ч", callback_data="history")]
    ])


async def send_history(chat_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/flights/history") as resp:
            data = await resp.json()

    flights = data.get("flights", [])
    if not flights:
        await bot.send_message(chat_id, "📭 История пуста")
        return

    lines = [f"📋 *История за 24 часа* — {len(flights)} рейсов\n"]
    for f in flights:
        t           = format_time(f.get("updated_at", ""))
        origin      = f.get("origin") or "???"
        destination = f.get("destination") or "???"
        callsign    = f.get("callsign") or "—"
        aircraft    = f.get("aircraft") or "—"
        alt         = f.get("altitude_ft")
        alt_str     = f"{alt:,} ft" if alt else "—"
        lines.append(f"*{callsign}* {origin}→{destination} {aircraft} {alt_str} `{t}`")

    await bot.send_message(chat_id, "\n".join(lines), parse_mode="Markdown")


async def send_to_all(photo_path: str, caption: str):
    logo = FSInputFile(photo_path)
    log.info(f"Sending to {len(subscribers)} subscribers")
    for chat_id in list(subscribers):
        try:
            await bot.send_photo(chat_id, photo=logo, caption=caption, parse_mode="Markdown")
            log.info(f"✅ Sent to {chat_id}")
        except Exception as e:
            log.error(f"Photo error {chat_id}: {type(e).__name__}: {e}")
            try:
                await bot.send_message(chat_id, caption, parse_mode="Markdown")
                log.info(f"✅ Text fallback sent to {chat_id}")
            except Exception as e2:
                log.error(f"Fallback error {chat_id}: {e2}")


# ── Handlers ─────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message):
    subscribers.add(message.chat.id)
    save_subscriber(message.chat.id)
    log.info(f"New subscriber: {message.chat.id}, total: {len(subscribers)}")
    await message.answer(
        "✈ *Rosh Pina Flight Tracker*\n\n"
        "Я буду присылать уведомления когда самолёт пролетает над домом.\n\n"
        "Используй кнопку ниже чтобы посмотреть историю за последние 24 часа.",
        parse_mode="Markdown",
        reply_markup=history_keyboard(),
    )


@dp.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery):
    await send_history(callback.message.chat.id)
    await callback.answer()


# ── Loops ─────────────────────────────────────────────────────────────────────

async def polling_loop():
    global notified
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(f"{API_URL}/flights") as resp:
                    data = await resp.json()

                current_ids = set()
                for flight in data.get("flights", []):
                    fid = flight["id"]
                    current_ids.add(fid)
                    if fid not in notified:
                        notified.add(fid)
                        text = format_flight(flight)
                        for chat_id in list(subscribers):
                            try:
                                await bot.send_message(
                                    chat_id, text,
                                    parse_mode="Markdown",
                                    reply_markup=history_keyboard()
                                )
                            except Exception as e:
                                log.error(f"Send error: {e}")

                notified &= current_ids

            except Exception as e:
                log.error(f"Polling error: {e}")

            await asyncio.sleep(POLL_INTERVAL)


async def oref_loop():
    global alerted
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(
                    f"{API_URL}/alerts",
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as resp:
                    if resp.status == 200:
                        data     = await resp.json()
                        active   = data.get("active", False)
                        areas    = data.get("areas", [])
                        title_he = data.get("title", "")
                        cat      = str(data.get("cat", ""))
                        title_en = TITLE_TRANSLATIONS.get(title_he, title_he)

                        if active:
                            current_alerts = set(areas)
                            new_areas = current_alerts - alerted

                            if new_areas:
                                areas_en = ", ".join(
                                    AREA_TRANSLATIONS.get(a, a) for a in new_areas
                                )

                                if cat in CAT_ENDED:
                                    caption = (
                                        f"✅ *All Clear*\n\n"
                                        f"Event has ended. See you next time! 🐕"
                                    )
                                    photo = LOGO_ENDED
                                elif cat in CAT_PREALERT:
                                    caption = (
                                        f"⚠️ *PRE-ALERT*\n"
                                        f"*{title_en}*\n\n"
                                        f"📍 {areas_en}\n\n"
                                        f"🏃 Please proceed to the nearest shelter!"
                                    )
                                    photo = LOGO_PREALERT
                                else:
                                    caption = (
                                        f"🚨 *RED ALERT*\n"
                                        f"*{title_en}*\n\n"
                                        f"📍 {areas_en}"
                                    )
                                    photo = LOGO_ALERT

                                log.info(f"🚨 Alert cat={cat} to {len(subscribers)} subs: {areas_en}")
                                await send_to_all(photo, caption)

                            alerted = current_alerts
                        else:
                            alerted = set()

            except Exception as e:
                log.error(f"Oref error: {e}")

            await asyncio.sleep(OREF_INTERVAL)


async def main():
    log.info(f"Bot started, loaded {len(subscribers)} subscribers from DB")
    asyncio.create_task(polling_loop())
    asyncio.create_task(oref_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())