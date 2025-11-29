# /opt/astro_bot/src/gen_alchemy_day_zodiac.py

import random
from datetime import date

from service_text import generate_text
from service_image import generate_image_for_topic
from dataclass_generated_post import GeneratedPost
from service_day_context import load_day_context
from service_zodiac_archetype import get_zodiac_archetype
from service_energy_personalization import get_energy_personalization
from service_tarot import draw_tarot_spread_with_image
from service_prompt_loader import get_prompt


def generate_alchemy_day_post(target_sign: str, post_date: date = None) -> GeneratedPost:
    """
    Генерирует пост "Астрологическая алхимия" для заданного знака на указанную дату.
    """
    post_date = post_date or date.today()

    # 1. Контекст дня
    context = load_day_context(post_date)

    # 2. Архетип знака
    archetype = get_zodiac_archetype(target_sign)

    # 3. Сбор архетипических напряжений как список
    tensions = [
        archetype.tension_control,
        archetype.tension_order,
        archetype.tension_speed
    ]
    tensions = [t for t in tensions if t]

    # 4. Персонализация: фаза + планета + знак Луны
    personalization = get_energy_personalization(
        sign=target_sign,
        moon_phase=context.moon_phase,
        moon_sign=context.moon_sign,
        planet=context.planet_of_day
    )
    personalization_blocks = "\n".join([
        f"🌕 {personalization.moon_phase.influence_value}: {personalization.moon_phase.message}" if personalization.moon_phase.message else "",
        f"🪐 {personalization.planet.influence_value}: {personalization.planet.message}" if personalization.planet.message else "",
        f"🌙 {personalization.moon_sign.influence_value}: {personalization.moon_sign.message}" if personalization.moon_sign.message else ""
    ]).strip()

    # 5. Случайная карта Таро
    cards, table_image_path = draw_tarot_spread_with_image("one")
    tarot_card = cards[0]
    card_meaning = tarot_card.reversed_text if tarot_card.reversed else tarot_card.upright_text

    # 6. Генерация текста через generate_text
    text = generate_text(
        topic_type="alchemy_day",
        theme=post_date,
        context={
            "sign": target_sign,
            "archetype": archetype.archetype,
            "element": archetype.element,
            "light": archetype.light,
            "shadow": archetype.shadow,
            "growth_strategy": archetype.growth_strategy,
            "tensions": tensions,
            "moon_phase": context.moon_phase,
            "moon_sign": context.moon_sign,
            "planet": context.planet_of_day,
            "card_name": tarot_card.name,
            "card_meaning": card_meaning,
            "personalization_blocks": personalization_blocks,
            "date": str(post_date)
        }
    )

    # 7. Генерация изображения через generate_image_for_topic
    topic = {
        "type": "alchemy_day",
        "theme": tarot_card,
        "target_sign": target_sign,
        "context": {
            "moon_phase": context.moon_phase,
            "planet": context.planet_of_day,
            "element": archetype.element,
            "card_name": tarot_card.name,
            "card_archetype": tarot_card.suit_archetype,
        }
    }
    image_path = generate_image_for_topic(topic)

    # 8. Порядок медиа: сначала «стол», затем сгенерированная картинка (если есть)
    images = []
    if table_image_path:
        images.append(table_image_path)
    if getattr(tarot_card, "image_path", None):
        images.append(tarot_card.image_path)
    if image_path:
        images.append(image_path)

    # 9. Возврат
    return GeneratedPost(
        type="alchemy_day",
        text=text,
        media_types={"image": images},
        metadata={"target_sign": target_sign, "theme": tarot_card.name, "date": str(post_date)}
    )
