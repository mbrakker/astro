# /opt/astro_bot/src/service_tarot.py
# -*- coding: utf-8 -*-
import os
import random
import sqlite3
from typing import List, Tuple, Optional
from datetime import datetime
from glob import glob
from zoneinfo import ZoneInfo  # ➕ детерминируем «день» по Europe/Paris

from dataclass_tarot import TarotCardDraw

# Внешний рендер «карт на столе» используем как библиотеку
# Универсальная функция поддерживает 1 или 3 карты
from service_tarot_ontable import compose_cards_keep_texture  # noqa: E402

TAROT_DB = "/opt/astro_bot/config/tarot.db"
CARDS_FOLDER = "/opt/astro_bot/tarot"

# Папка фонов-столов
SCARLET_TABLE_DIR = "/opt/astro_bot/tarot/scarlet_table"

# Куда складывать готовые изображения раскладов
TAROT_OUT_DIR = "/opt/astro_bot/images/tarot"


def load_all_card_ids() -> list[str]:
    conn = sqlite3.connect(TAROT_DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM tarot_cards")
    return [row[0] for row in cur.fetchall()]


def load_card_by_id(card_id: str) -> dict:
    conn = sqlite3.connect(TAROT_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM tarot_cards WHERE id = ?", (card_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Карта {card_id} не найдена.")
    return dict(row)


def get_card_image_path(card: dict, is_reversed: bool = False) -> str:
    """
    Возвращает путь к изображению карты.
    Если карта перевёрнута, путь указывает на подпапку 'reverse' и имя файла
    дополняется суффиксом '_reversed' перед расширением.
    """
    base_folder = CARDS_FOLDER
    filename = card["image_path"]

    if is_reversed:
        base_folder = os.path.join(CARDS_FOLDER, "reverse")
        root, ext = os.path.splitext(filename)
        filename = f"{root}_reversed{ext}"

    return os.path.join(base_folder, filename)


def draw_tarot_spread(spread_type: str = "one") -> List[TarotCardDraw]:
    """
    Возвращает список из 1 или 3 карт в виде TarotCardDraw.
    """
    used_ids = set()
    result: List[TarotCardDraw] = []

    if spread_type == "one":
        count = 1
        positions = [None]
    elif spread_type == "three":
        count = 3
        positions = ["Прошлое", "Настоящее", "Будущее"]
    else:
        raise ValueError(f"Неизвестный тип расклада: {spread_type}")

    all_ids = load_all_card_ids()
    while len(result) < count:
        card_id = random.choice(all_ids)
        if card_id in used_ids:
            continue
        used_ids.add(card_id)
        raw = load_card_by_id(card_id)
        is_reversed = random.choice([True, False])
        position = positions[len(result)]

        result.append(
            TarotCardDraw(
                id=raw["id"],
                name=raw["name"],
                arcana=raw["arcana"],
                suit=raw.get("suit"),
                number=raw.get("number"),
                reversed=is_reversed,
                upright_text=raw.get("upright_text"),
                reversed_text=raw.get("reversed_text"),
                suit_archetype=raw.get("suit_archetype"),
                number_archetype=raw.get("number_archetype"),
                position=position,
                image_path=get_card_image_path(raw, is_reversed)
            )
        )

    return result


def _pick_daily_seed_from_dir(date_str: str) -> str:
    """
    Детерминированно выбираем файл scarlet_table*.jpg в каталоге столов
    на дату date_str (формат YYYYMMDD). Для воспроизводимости в течение суток
    используем локальный генератор random.Random(date_str).
    """
    pattern = os.path.join(SCARLET_TABLE_DIR, "scarlet_table*.jpg")
    candidates = sorted(glob(pattern))
    # Совместимость с именем без номера
    fallback = os.path.join(SCARLET_TABLE_DIR, "scarlet_table.jpg")
    if not candidates and os.path.exists(fallback):
        candidates = [fallback]
    if not candidates:
        raise FileNotFoundError(
            f"Не найдено ни одного фона scarlet_table*.jpg в {SCARLET_TABLE_DIR}"
        )
    # Локальный генератор — не влияет на глобальный random.
    rnd = random.Random(date_str)
    return rnd.choice(candidates)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def draw_tarot_spread_with_image(spread_type: str = "three") -> Tuple[List[TarotCardDraw], str]:
    """
    Расширенная версия: кроме списка карт возвращает путь к итоговой картинке
    с визуализацией «на столе».

    Возвращает:
        (cards: List[TarotCardDraw], out_image_path: str)
    """
    # 1) Тянем карты стандартным способом (обратная совместимость полностью сохранена)
    cards = draw_tarot_spread(spread_type=spread_type)

    # 2) Готовим пути к исходникам карт:
    #    on-table сам будет добавлять _reversed при необходимости, поэтому
    #    передаём UPRIGHT-пути и список флагов reversed.
    upright_paths: List[str] = []
    reversed_flags: List[bool] = []
    for c in cards:
        raw = load_card_by_id(c.id)
        upright_paths.append(get_card_image_path(raw, is_reversed=False))
        reversed_flags.append(bool(c.reversed))

    # 3) Фон-стол детерминированный на день (таймзона Europe/Paris)
    date_str = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y%m%d")
    seed_path = _pick_daily_seed_from_dir(date_str)

    # 4) Путь сохранения
    _ensure_dir(TAROT_OUT_DIR)
    card_ids = "-".join([c.id for c in cards])
    out_name = f"{date_str}_spread-{spread_type}_{card_ids}.jpg"
    out_path = os.path.join(TAROT_OUT_DIR, out_name)

    # 5) Вызов on-table как библиотеки (без CLI)
    #    Универсальная функция поддерживает 1 или 3 карты и сохраняет JPEG с качеством 96.
    compose_cards_keep_texture(
        seed_path=seed_path,
        card_paths=upright_paths,
        out_path=out_path,
        reversed_flags=reversed_flags,
        angle_jitter_deg=1.0,
        pos_jitter_px=4,
        allow_upscale=False,
        add_grain=False,
        grain_strength=0.0,
    )

    return cards, out_path


# -----------------------------
# 🔹 Мини-добавка по задаче
# -----------------------------
def assemble_image_list(cards: List[TarotCardDraw], table_image: Optional[str] = None) -> List[str]:
    """
    Возвращает список путей к изображениям карт.
    Если передан table_image (путь к «раскладу на столе»), добавляет его в конец списка.

    Использование:
        cards, table_img = draw_tarot_spread_with_image("three")
        images_to_send = assemble_image_list(cards, table_img)
    """
    paths = [c.image_path for c in cards]
    if table_image:
        paths.append(table_image)
    return paths
