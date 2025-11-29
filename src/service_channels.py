# /opt/astro_bot/src/service_channels.py

import os
from dotenv import load_dotenv

load_dotenv("/opt/astro_bot/env/.env")

# Основной канал (общий гороскоп, мистика, откровения и т.д.)
MAIN_CHANNEL = os.getenv("TELEGRAM_CHAT_ID")

# Маппинг знаков зодиака к Telegram-каналам
ZODIAC_CHANNELS = {
    "овен": os.getenv("TG_CHANNEL_SCARLET_OVEN"),
    "телец": os.getenv("TG_CHANNEL_SCARLET_TELEC"),
    "близнецы": os.getenv("TG_CHANNEL_SCARLET_BLIZNECY"),
    "рак": os.getenv("TG_CHANNEL_SCARLET_RAK"),
    "лев": os.getenv("TG_CHANNEL_SCARLET_LEV"),
    "дева": os.getenv("TG_CHANNEL_SCARLET_DEVA"),
    "весы": os.getenv("TG_CHANNEL_SCARLET_VESY"),
    "скорпион": int(os.getenv("TG_CHANNEL_SCARLET_SKORPION")),
    "стрелец": int(os.getenv("TG_CHANNEL_SCARLET_STRELEC")),
    "козерог": int(os.getenv("TG_CHANNEL_SCARLET_KOZEROG")),
    "водолей": int(os.getenv("TG_CHANNEL_SCARLET_VODOLEY")),
    "рыбы": int(os.getenv("TG_CHANNEL_SCARLET_RYBY")),
}
