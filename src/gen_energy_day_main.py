# /opt/astro_bot/src/gen_energy_day_main.py
import datetime
import os
import glob
import logging
from service_text import generate_text
from service_notifier import notify_owner_async
from dataclass_generated_post import GeneratedPost
from service_day_context import DayContext  # Новый импорт

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----- Загрузка параметров из DayContext -----
def get_energy_day_params(date: datetime.date = None):
    date = date or datetime.date.today()
    context = DayContext.load(date)

    # Подмена moon_sign, если неизвестно
    if context.moon_sign.lower() == "Неизвестно":
        moon_sign = f"сегодня {context.lunar_day} лунный день"
    else:
        moon_sign = context.moon_sign.lower()

    return {
        "moon_phase": context.moon_phase.lower(),
        "moon_sign": moon_sign,
        "planet_of_day": context.planet_of_day.lower()
    }

# ----- Загрузка изображений по дате -----
def download_all_energy_images(date: datetime.date = None) -> list:
    """
    Ищет все изображения Stellarium по дате публикации.
    """
    date = date or datetime.date.today()
    pattern = f"/opt/astro_bot/images/energy/{date.isoformat()}_*.png"
    return sorted([f for f in glob.glob(pattern) if os.path.isfile(f)])

# ----- Генерация текста и итоговая функция -----
async def generate_energy_day_post() -> GeneratedPost:
    """
    Генерирует пост рубрики «Энергия дня» в формате GeneratedPost.
    """
    logger.info("⚡️ Генерация поста 'Энергия дня' началась")

    try:
        date = datetime.date.today()
        params = get_energy_day_params(date)
        text = generate_text(
            topic_type="energy_day",
            context=params
        )
        image_paths = download_all_energy_images(date)

        if not image_paths:
            raise RuntimeError("❌ Не найдено ни одного изображения Stellarium")

        logger.info(f"✅ Генерация завершена: {len(image_paths)} изображений")

        return GeneratedPost(
            type="energy_day",
            text=text,
            media_types={"image": image_paths},
            metadata=params
        )

    except Exception as e:
        logger.exception(f"❌ Ошибка в generate_energy_day_post(): {e}")
        await notify_owner_async(f"❌ Ошибка публикации 'Энергия дня': {e}")
        raise
