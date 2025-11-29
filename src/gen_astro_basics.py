# /opt/astro_bot/src/gen_astro_basics.py

import os
from service_text import generate_text
from service_image import generate_image_for_topic
from dataclass_generated_post import GeneratedPost

IMAGES_FOLDER = "/opt/astro_bot/images/astro_basics"
os.makedirs(IMAGES_FOLDER, exist_ok=True)

def generate_astro_basic_post(theme: str) -> GeneratedPost:
    """
    Генерирует пост с азами астрологии.
    Возвращает GeneratedPost.
    """
    text = generate_text(
        topic_type="astro_basics",
        theme=theme,
        context={"theme": theme}
    )

    prefix = theme.strip().replace(" ", "_").lower()

    topic = {
        "type": "astro_basics",
        "theme": theme,
        "context": {"prefix": prefix}
    }

    image_path = generate_image_for_topic(topic)

    if image_path and os.path.isfile(image_path):
        filename = f"{prefix}.png"
        new_path = os.path.join(IMAGES_FOLDER, filename)
        os.rename(image_path, new_path)
        image_path = new_path
    else:
        filename = None

    return GeneratedPost(
        type="astro_basics",
        text=text,
        media_types={"image": [image_path]} if image_path else {},
        metadata={
            "theme": theme,
            "prefix": prefix,
            "image_filename": filename
        }
    )
