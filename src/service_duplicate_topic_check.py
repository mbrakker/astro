# /opt/astro_bot/src/service_duplicate_topic_check.py
# -*- coding: utf-8 -*-

import sqlite3
from service_history_logger import is_already_published, make_hash
import datetime

DUPLICATE_LOG = "/opt/astro_bot/logs/duplicates.log"

def is_duplicate_topic(topic: dict) -> bool:
    """
    Проверяет, была ли уже публикация аналогичного контента, в зависимости от типа
    Логирует дубли в отдельный файл
    """
    t_type = topic["type"]
    date = topic.get("scheduled_for")
    sign = topic.get("target_sign")
    theme = topic.get("theme")
    context = topic.get("context") or {}
    source = context.get("source_url")
    text = topic.get("text", "")
    hash_text = make_hash(text) if text else None

    is_dup = False

    if t_type in ["horoscope", "energy_day"]:
        is_dup = _exists_post(type=t_type, date=date)

    elif t_type == "zodiac_energy":
        is_dup = _exists_post(type=t_type, date=date, sign=sign)

    elif t_type == "tarot_weekly":
        is_dup = _exists_post(type=t_type, date=date, theme="tarot_weekly")

    elif t_type == "mystic_news":
        is_dup = is_already_published(source_hash=make_hash(source or ""),
                                      title_hash=make_hash(theme or ""),
                                      text_hash=hash_text)

    elif t_type == "confession":
        is_dup = _exists_post(type=t_type, theme=theme)

    elif t_type == "astro_basics":
        is_dup = _exists_post(type=t_type, theme=theme, sign=sign)

    if is_dup:
        _log_duplicate(topic)

    return is_dup


def _exists_post(**filters) -> bool:
    query = "SELECT COUNT(*) FROM posts WHERE 1=1"
    params = []
    for key, value in filters.items():
        if value is not None:
            query += f" AND {key} = ?"
            params.append(value)

    conn = sqlite3.connect("/opt/astro_bot/history/posts.db")
    cur = conn.cursor()
    cur.execute(query, params)
    result = cur.fetchone()[0]
    conn.close()
    return result > 0


def _log_duplicate(topic: dict):
    try:
        with open(DUPLICATE_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] Дубль: {topic['type']} | {topic.get('scheduled_for')} | {topic.get('theme')} | {topic.get('target_sign')}\n")
    except Exception:
        pass
