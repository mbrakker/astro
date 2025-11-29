# /opt/astro_bot/src/gen_tarot_weekly.py
# -*- coding: utf-8 -*-
import logging
import json
from typing import List

# ⬇️ минимальная правка: берём функцию, которая ещё и рендерит «стол»
from service_tarot import draw_tarot_spread_with_image
from service_text import generate_text
from dataclass_generated_post import GeneratedPost
from dataclass_tarot import TarotCardDraw

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_path = "/opt/astro_bot/logs/bot.log"
handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

def generate_tarot_weekly_post() -> GeneratedPost:
    logger.info("🔮 [tarot_weekly_gen] Запрос расклада из 3 карт")
    # ⬇️ минимальная правка: получаем и карты, и путь к общему изображению «на столе»
    cards, table_image_path = draw_tarot_spread_with_image("three")
    card_contexts = []

    for card in cards:
        logger.info(
            f"🃏 Карта: {card.id} — {card.position}: {card.name} ({'Перевёрнутая' if card.reversed else 'Прямая'})"
        )

        interpretation = card.get_interpretation()

        if not interpretation or interpretation == "🔮 Карта скрывает свою тайну…":
            logger.warning(f"⚠️ У карты {card.id} нет трактовки: reversed={card.reversed}")

        card_contexts.append({
            "card_id": card.id,
            "card_name": card.name,
            "arcana": card.arcana,
            "suit": card.suit,
            "number": card.number,
            "reversed": card.reversed,
            "position": card.position,
            "interpretation": interpretation,
            "suit_archetype": card.suit_archetype,
            "number_archetype": card.number_archetype,
        })

    context = {"cards": card_contexts}

    logger.info("📦 [tarot_weekly_gen] Формирование контекста для генерации поста")
    logger.info("📋 Контекст карт перед GPT:")
    logger.info(json.dumps(context, ensure_ascii=False, indent=2))

    text = generate_text(
        topic_type="tarot_weekly",
        theme="Таро недели",
        context=context
    ).strip()

    # ⬇️ ключевая правка порядка: СНАЧАЛА «стол», потом отдельные карты
    image_paths = []  # type: List[str]
    if table_image_path:
        image_paths.append(table_image_path)
        logger.info(f"🖼️ Общее изображение стола поставлено ПЕРВЫМ: {table_image_path}")

    image_paths.extend([card.image_path for card in cards if getattr(card, "image_path", None)])

    logger.info("✅ [tarot_weekly_gen] Пост успешно сгенерирован")

    return GeneratedPost(
        type="tarot",
        text=text,
        media_types={"image": image_paths},
        metadata={
            "cards": [card.__dict__ for card in cards],
            "positions": [card.position for card in cards],
            "context": context
        }
    )

if __name__ == "__main__":
    post = generate_tarot_weekly_post()
    print(post.text)
    print("\n📸 Изображения:")
    for img in post.media_types.get("image", []):
        print(" -", img)
