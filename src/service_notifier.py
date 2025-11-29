# /opt/astro_bot/src/service_notifier.py

import os
import logging
import requests
import aiohttp
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv(dotenv_path="/opt/astro_bot/env/.env")

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Параметры Telegram бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("TELEGRAM_OWNER_ID")

# --- Синхронное уведомление (для тестов, совместимости) ---

def notify_owner(message: str) -> None:
    """Синхронное уведомление владельцу через Telegram Bot API."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": OWNER_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        logger.info("📨 Синхронное уведомление отправлено владельцу")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки синхронного уведомления владельцу: {e}")

# --- Асинхронное уведомление (для пайплайна) ---

async def notify_owner_async(message: str) -> None:
    """Асинхронное уведомление владельцу через Telegram Bot API."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": OWNER_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"❌ Ошибка при отправке асинхронного уведомления владельцу: {response.status}")
                else:
                    logger.info("📨 Асинхронное уведомление отправлено владельцу")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки асинхронного уведомления владельцу: {e}")
