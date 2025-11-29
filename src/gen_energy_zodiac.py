# /opt/astro_bot/src/gen_zodiac_energy.py
# -*- coding: utf-8 -*-
import datetime
import os
import logging
import glob
from service_text import generate_text
from service_day_context import load_day_context
from dataclass_generated_post import GeneratedPost
from service_energy_personalization import get_energy_personalization
from dataclass_energy_personalization import EnergyPersonalization

def get_moon_screenshot_path(date: datetime.date = None, which: int = 1) -> str:
    """
    Ищет любое изображение Луны, сгенерированное по дате.
    Совместим с произвольными названиями: 2025-06-08_*.png
    """
    date = date or datetime.date.today()
    pattern = f"/opt/astro_bot/images/energy/{date.isoformat()}_*.png"
    for path in sorted(glob.glob(pattern)):
        if os.path.isfile(path):
            return path
    return ""

async def generate_zodiac_energy_post(sign: str) -> GeneratedPost:
    """
    Генерирует персонализированный пост энергии дня для знака зодиака.
    Возвращает GeneratedPost.
    """
    date = datetime.date.today()
    context = load_day_context(date)

    moon_phase = context.moon_phase.lower()
    moon_sign = context.moon_sign.lower()
    planet = context.planet_of_day.lower()

    personalization = get_energy_personalization(
        sign=sign,
        moon_phase=moon_phase,
        moon_sign=moon_sign,
        planet=planet
    )

    context_data = {
        "sign": sign,
        "moon_phase": moon_phase,
        "moon_sign": (
            f"сегодня {context.lunar_day} лунный день"
            if moon_sign == "неизвестно"
            else moon_sign
        ),
        "planet_of_day": planet,
        "tone1": personalization.moon_phase.tone,
        "message1": personalization.moon_phase.message,
        "tone2": personalization.moon_sign.tone,
        "message2": personalization.moon_sign.message,
        "tone3": personalization.planet.tone,
        "message3": personalization.planet.message
    }

    text = generate_text(
        topic_type="zodiac_energy",
        context=context_data
    )

    image_path = None
    for which in [1, 2]:
        path = get_moon_screenshot_path(date, which)
        if path:
            image_path = path
            break

    if not image_path:
        logging.getLogger(__name__).warning("⚠️ Нет изображения Луны для zodiac_energy — пост будет без картинки")

    return GeneratedPost(
        type="zodiac_energy",
        text=text,
        media_types={"image": [image_path]} if image_path else {},
        metadata={
            "sign": sign,
            "moon_phase": moon_phase,
            "moon_sign": moon_sign,
            "planet": planet
        }
    )
