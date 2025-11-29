# /opt/astro_bot/src/service_image.py
# -*- coding: utf-8 -*-
import os
import hashlib
import random
import requests
from openai import OpenAI
from dotenv import load_dotenv
from service_prompt_loader import get_prompt
from service_history_logger import make_hash
from service_openai_logger import log_openai_usage
from service_notifier import notify_owner
from service_prompt_loader import _load_config
import logging

# Загрузка .env
load_dotenv("/opt/astro_bot/env/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("/opt/astro_bot/logs/bot.log")
handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(handler)

# Папка с изображениями
IMAGE_ROOT = "/opt/astro_bot/images"

# Карта: тип контента → ключ в prompts.yaml
DALL_E_TEMPLATE_MAP = {
    "confession": "confession_prompt_templates",
    "astro_basics": "astro_basics_prompt_templates",
    "mystic": "mystic_prompt_templates",
    "horoscope": "horoscope_prompt_templates",
    "zodiac_energy": "zodiac_energy_prompt_templates",
    "energy": "energy_prompt_templates",
    "news_all": "news_all_prompt_templates",
    "news_astro": "news_astro_prompt_templates",
    "alchemy_day": "alchemy_day_prompt_templates",
    "news_horoscope": "news_horoscope_prompt_templates",
    "education": "education_prompt_templates",
    "open_slot": "open_slot_prompt_templates"
}

def build_prompt(topic: dict) -> tuple[str, str]:
    topic_type = topic["type"]
    context = topic.get("context", {}) or {}
    dalle_key = DALL_E_TEMPLATE_MAP.get(topic_type)

    if not dalle_key:
        raise ValueError(f"❌ Неизвестный тип контента для DALL·E: {topic_type}")

    # Добавляем theme и sign в context
    prompt_vars = context.copy()
    prompt_vars["theme"] = topic.get("theme") or "<NO_THEME>"
    prompt_vars["sign"] = topic.get("target_sign") or "<NO_SIGN>"
    prompt_vars["raw_text"] = context.get("raw_text") or topic.get("raw_text") or "<NO_RAW_TEXT>"
    prompt_vars["color_palette"] = context.get("color_palette") or "cosmic gold"

    # Добавляем для DALL·E-промптов новостей
    if topic["type"] in ["mystic", "news_all", "news_astro", "news_horoscope", "education", "open_slot"]:
        prompt_vars["news_title"] = topic.get("theme", "<NO_TITLE>")

    # Для отладки — выводим весь контекст, который пойдёт в шаблон
    logger.info(f"[DEBUG] DALL·E build_prompt context: {prompt_vars}")

    cfg = _load_config()
    section = cfg.get("dalle", {})
    prompt_list = section.get(dalle_key, [])
    if not prompt_list:
        raise ValueError(f"❌ В prompts.yaml нет шаблонов для {dalle_key}")
    prompt = random.choice(prompt_list).format(**prompt_vars)

    if not prompt or not prompt.strip():
        raise ValueError(f"❌ Пустой prompt для DALL·E ({topic_type}, {dalle_key}), context={prompt_vars}")

    return prompt, topic_type

def download_image(image_url: str, save_path: str):
    response = requests.get(image_url)
    response.raise_for_status()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(response.content)
    logger.info(f"📸 Картинка сохранена: {save_path}")

def get_cached_path(topic_type: str, prompt: str) -> str:
    prompt_hash = make_hash(prompt)
    return os.path.join(IMAGE_ROOT, topic_type, f"{prompt_hash}.png")

def generate_image_for_topic(topic: dict) -> str:
    """
    Генерация изображения через DALL·E по данным из topic.
    Возвращает путь к локальному файлу или "" при ошибке.
    """
    try:
        prompt, topic_type = build_prompt(topic)
        image_path = get_cached_path(topic_type, prompt)

        if os.path.isfile(image_path):
            logger.info(f"♻️ Используем кеш: {image_path}")
            return image_path

        logger.info(f"🎨 Запрос к DALL·E для темы: {topic.get('theme')}")
        logger.info(f"📜 Промпт: {prompt[:200]}...")

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        image_url = response.data[0].url
        download_image(image_url, image_path)

        log_openai_usage(action_type="image_generation", images_generated=1)

        logger.info(f"✅ Изображение успешно сгенерировано: {image_path}")
        return image_path

    except Exception as e:
        logger.exception(f"❌ Ошибка генерации изображения для темы {topic.get('theme')}: {e}")
        notify_owner(f"❌ Ошибка генерации изображения для темы «{topic.get('theme')}»: {e}")
        return ""
