# /opt/astro_bot/src/services/service_telegram_sender.py
# -*- coding: utf-8 -*-
import os
import logging
import datetime
import locale
from dotenv import load_dotenv
from telethon import TelegramClient
from service_notifier import notify_owner
from service_channels import MAIN_CHANNEL, ZODIAC_CHANNELS
from dataclass_generated_post import GeneratedPost

# Подгружаем .env
load_dotenv(dotenv_path="/opt/astro_bot/env/.env")

# Настройка логирования
logger = logging.getLogger(__name__)

# Параметры Telethon
API_ID = int(os.getenv("TELETHON_API_ID"))
API_HASH = os.getenv("TELETHON_API_HASH")
SESSION_NAME = os.getenv("TELETHON_SESSION", "astro_bot_session")

# Глобальный клиент
_client = None

async def get_telegram_client():
    global _client
    if _client is None:
        session_path = f'/opt/astro_bot/sessions/{SESSION_NAME}'
        _client = TelegramClient(session_path, API_ID, API_HASH)
        await _client.start()
    return _client

# Перевод знаков зодиака на русский
ZODIAC_TRANSLATIONS = {
    "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы", "cancer": "Рак",
    "leo": "Лев", "virgo": "Дева", "libra": "Весы", "scorpio": "Скорпион",
    "sagittarius": "Стрелец", "capricorn": "Козерог", "aquarius": "Водолей", "pisces": "Рыбы"
}

EN_TO_RU = {
    "aries": "овен", "taurus": "телец", "gemini": "близнецы", "cancer": "рак",
    "leo": "лев", "virgo": "дева", "libra": "весы", "scorpio": "скорпион",
    "sagittarius": "стрелец", "capricorn": "козерог", "aquarius": "водолей", "pisces": "рыбы"
}

def resolve_channel(channel_scope: str, target_sign: str = None) -> str:
    if channel_scope == "main":
        return MAIN_CHANNEL
    elif channel_scope == "zodiac":
        if not target_sign:
            raise ValueError("❌ channel_scope=zodiac требует target_sign")
        key = EN_TO_RU.get(target_sign.lower(), target_sign.lower())
        channel = ZODIAC_CHANNELS.get(key)
        if not channel:
            raise ValueError(f"❌ Неизвестный знак зодиака: {target_sign}")
        return channel
    else:
        raise ValueError(f"❌ Неизвестный channel_scope: {channel_scope}")

def get_russian_date() -> str:
    try:
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    except locale.Error:
        pass
    today = datetime.date.today()
    return today.strftime("%A, %d %B").capitalize()

from telethon import TelegramClient

async def post_to_telegram(
    type: str,
    text: str,
    media_types: dict[str, list[str]],
    theme: str = None,
    target_sign: str = None,
    scope: str = "main"
) -> None:
    """
    Универсальный метод публикации любого контента в Telegram.
    """

    API_ID = int(os.getenv("TELETHON_API_ID"))
    API_HASH = os.getenv("TELETHON_API_HASH")
    SESSION_NAME = os.getenv("TELETHON_SESSION", "astro_bot_session")

    try:
        async with TelegramClient(f'/opt/astro_bot/sessions/{SESSION_NAME}', API_ID, API_HASH) as client:
            date_str = get_russian_date()

            if type == "confession":
                header = f"<b>🔥 Откровения Скарлет: {theme}</b>"
                caption = f"{header}\n\n{text}\n\n✨ #СкарлетЛуна"

            elif type == "astro_basic":
                header = f"<b>🔮 Азы астрологии: {theme}</b>"
                caption = f"{header}\n\n{text}\n\n✨ #СкарлетЛуна"

            elif type == "energy":
                header = f"<b>🌙 Энергия дня — {date_str}</b>"
                caption = f"{header}\n\n{text}\n\n✨ #СкарлетЛуна"

            elif type == "zodiac_energy":
                sign_rus = ZODIAC_TRANSLATIONS.get((target_sign or "").lower(), target_sign or "Знак")
                header = f"<b>🌙 Энергия дня для {sign_rus}</b>\n<i>{date_str}</i>"
                caption = f"{header}\n\n{text}\n\n✨ #СкарлетЛуна"

            elif type == "tarot":
                header = f"<b>🃏 Таро недели — {date_str}</b>"
                caption = f"{header}\n\n{text}\n\n✨ #СкарлетЛуна"

            elif type == "horoscope":
                sign_rus = ZODIAC_TRANSLATIONS.get((target_sign or "").lower(), target_sign or "Знак")
                parts = text.strip().split('🌟')
                main_text = parts[0].strip()
                mantra_and_sovet = '🌟' + parts[1].strip() if len(parts) > 1 else ''
                if "🔮" in mantra_and_sovet:
                    mantra_text, sovet_text = mantra_and_sovet.split("🔮", 1)
                    mantra_text = mantra_text.strip()
                    sovet_text = "🔮" + sovet_text.strip()
                else:
                    mantra_text = mantra_and_sovet.strip()
                    sovet_text = ""
                caption = (
                    f"<b>🔮 {sign_rus}</b>\n<i>{date_str}</i>\n\n"
                    f"{main_text}\n\n{mantra_text}\n\n{sovet_text}\n\n✨ #СкарлетЛуна"
                )

            elif type == "mystic":
                title = theme or "Загадка дня"
                header = f"<b>🌌 Новости между мирами: {title}</b>"
                caption = f"{header}\n\n{text}\n\n✨ #СкарлетЛуна"

            else:
                header = f"<b>✨ {theme or 'Публикация'}</b>"
                caption = f"{header}\n\n{text}\n\n✨ #СкарлетЛуна"

            entity = resolve_channel(scope, target_sign)

            files = []
            for group in ["image", "video", "audio"]:
                files.extend(media_types.get(group, []))

            if not files:
                raise ValueError("❌ Нет медиафайлов для публикации")

            await client.send_file(
                entity=entity,
                file=files,
                caption=caption,
                parse_mode="html"
            )

            logger.info(f"✅ Публикация '{type}' успешно отправлена")

    except Exception as e:
        logger.exception(f"❌ Ошибка публикации '{type}': {e}")
        notify_owner(f"❌ Ошибка публикации '{type}': {e}")

async def post_generated_post(post: GeneratedPost, scope: str = "main", target_sign: str = None) -> None:
    await post_to_telegram(
        type=post.type,
        text=post.text,
        media_types=post.media_types,
        theme=post.metadata.get("theme"),
        target_sign=target_sign or post.metadata.get("target_sign"),
        scope=scope
    )
