# /opt/astro_bot/src/gen_confession.py
# -*- coding: utf-8 -*-
import os
from service_text import generate_text
from service_image import generate_image_for_topic
from service_openai_logger import log_openai_usage
from dataclass_generated_post import GeneratedPost

IMAGES_FOLDER = "/opt/astro_bot/images/confessions"
os.makedirs(IMAGES_FOLDER, exist_ok=True)

def generate_confession_post(theme: str) -> GeneratedPost:
    """
    Генерирует откровение Скарлет (текст + изображение) по теме.
    Возвращает объект GeneratedPost.
    """
    context = {"theme": theme}
    text = generate_text(topic_type="confession", theme=theme, context=context)

    prefix = theme.replace(" ", "_").lower()
    topic = {
        "type": "confession",
        "theme": theme,
        "context": {"prefix": prefix}
    }

    image_path = generate_image_for_topic(topic)

    # Переименуем файл для хранения с фиксированным именем
    if image_path and os.path.isfile(image_path):
        new_path = os.path.join(IMAGES_FOLDER, f"{prefix}.png")
        os.rename(image_path, new_path)
        image_path = new_path

    return GeneratedPost(
        type="confession",
        text=text,
        media_types={"image": [image_path]} if image_path else {},
        metadata={"theme": theme}
    )
