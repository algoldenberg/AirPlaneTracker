import os
import logging
import asyncio
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
POLL_INTERVAL = 10
OREF_URL      = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
OREF_INTERVAL = 5
TARGET_AREAS  = ["תל אביב - דרום", "תל אביב"]

bot = Bot(token=TOKEN)
dp  = Dispatcher()

subscribers: set[int] = set()
notified:    set[str] = set()
alerted:     set[str] = set()  # активные тревоги чтобы не спамить


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


@dp.message(CommandStart())
async def cmd_start(message: Message):
    subscribers.add(message.chat.id)
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
                        for chat_id in subscribers:
                            try:
                                # Уведомление о рейсе + кнопка истории
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
    """Фоновая задача — проверяет тревоги Цева Адом каждые 5 секунд."""
    global alerted
    headers = {
        "Referer": "https://www.oref.org.il/",
        "X-Requested-With": "XMLHttpRequest",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            try:
                async with session.get(OREF_URL, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if text.strip():
                            data = await resp.json(content_type=None)
                            areas = data.get("data", [])
                            current_alerts = set()

                            for area in areas:
                                if any(target in area for target in TARGET_AREAS):
                                    current_alerts.add(area)
                                    if area not in alerted:
                                        log.info(f"🚨 Alert: {area}")
                                        for chat_id in subscribers:
                                            try:
                                                await bot.send_message(
                                                    chat_id,
                                                    f"🚨 *ЦЕВА АДОМ!*\n\n📍 {area}",
                                                    parse_mode="Markdown"
                                                )
                                            except Exception as e:
                                                log.error(f"Alert send error: {e}")

                            alerted = current_alerts
                        else:
                            alerted = set()

            except Exception as e:
                log.error(f"Oref error: {e}")

            await asyncio.sleep(OREF_INTERVAL)


async def main():
    log.info("Bot started")
    asyncio.create_task(polling_loop())
    asyncio.create_task(oref_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())