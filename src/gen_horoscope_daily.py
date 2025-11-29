# /opt/astro_bot/src/gen_horoscope_daily.py
from dataclass_generated_post import GeneratedPost
import requests
from service_text import generate_text
from service_image import generate_image_for_topic

HOROSCOPE_API_URL = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"

RUSSIAN_SIGNS = {
    "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы", "cancer": "Рак", "leo": "Лев", "virgo": "Дева",
    "libra": "Весы", "scorpio": "Скорпион", "sagittarius": "Стрелец", "capricorn": "Козерог",
    "aquarius": "Водолей", "pisces": "Рыбы"
}


def get_raw_horoscope(sign: str) -> str:
    url = f"{HOROSCOPE_API_URL}?sign={sign.lower()}&day=today"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("horoscope_data", "")


def transform_to_scarlet_style(raw_text: str, sign: str) -> str:
    return generate_text(
        topic_type="horoscope",
        theme=raw_text,
        context={
            "sign": RUSSIAN_SIGNS.get(sign.lower(), sign.capitalize()),
            "raw_text": raw_text
        }
    )


def generate_horoscope_post(sign: str, date: str) -> GeneratedPost:
    """
    Генерирует гороскоп в стиле Скарлет. Возвращает объект GeneratedPost.
    """
    raw_text = get_raw_horoscope(sign)
    text = transform_to_scarlet_style(raw_text, sign)

    topic_stub = {
        "type": "horoscope",
        "target_sign": sign,
        "theme": raw_text,
        "context": {
            "date": date,
            "sign": sign,
            "raw_text": raw_text,
            "color_palette": "cosmic gold"
        }
    }
    image_path = generate_image_for_topic(topic_stub)

    return GeneratedPost(
        type="horoscope",
        text=text,
        media_types={"image": [image_path]} if image_path else {},
        metadata={
            "target_sign": sign,
            "date": date,
            "raw_text": raw_text
        }
    )
