# /opt/astro_bot/src/script_preload_stellarium.py
# -*- coding: utf-8 -*-
import datetime
import logging
from service_stellarium import get_stellarium_images

# Настройка логгера
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("/opt/astro_bot/logs/preload.log"),
        logging.StreamHandler()
    ]
)

def get_planet_of_day(date: datetime.date) -> str:
    weekday = date.weekday()
    return {
        0: "луна",
        1: "марс",
        2: "меркурий",
        3: "юпитер",
        4: "венера",
        5: "сатурн",
        6: "солнце"
    }[weekday]

if __name__ == "__main__":
    logger.info("🛰 Начало предзагрузки Stellarium")
    try:
        target_date = datetime.date.today() + datetime.timedelta(days=1)
        planet = get_planet_of_day(target_date)
        paths = get_stellarium_images(target_date, planet)
        logger.info(f"✅ Успешно сгенерировано {len(paths)} изображений для {target_date} ({planet})")
    except Exception as e:
        logger.exception(f"❌ Ошибка при предзагрузке Stellarium: {e}")
