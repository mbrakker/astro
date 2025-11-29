# /opt/astro_bot/src/service_history_logger.py
# -*- coding: utf-8 -*-
import os
import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "/opt/astro_bot/history/posts.db"

def init_db():
    """Создаёт файл БД и таблицу posts один раз, если их ещё нет."""
    if os.path.isfile(DB_PATH):
        return
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            source_url_hash TEXT,
            title_hash TEXT,
            text_hash TEXT,
            created_at DATETIME,
            published_at DATETIME
        )
    """)
    conn.commit()
    conn.close()

def make_hash(text: str) -> str:
    """Возвращает MD5-хэш от произвольного текста."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def is_already_published(source_hash: str, title_hash: str, text_hash: str) -> bool:
    """
    Проверяет, встречался ли ранее хоть один из трёх хэшей.
    Возвращает True, если запись найдена (любое совпадение).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM posts WHERE source_url_hash = ? OR title_hash = ? OR text_hash = ?",
        (source_hash, title_hash, text_hash)
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def log_post(post_type: str, source_hash: str, title_hash: str, text_hash: str):
    """
    Записывает новую публикацию в таблицу.
    INSERT OR IGNORE предотвращает дублирование по уникальным хэшам.
    """
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO posts
          (type, source_url_hash, title_hash, text_hash, created_at, published_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (post_type, source_hash, title_hash, text_hash, now, now))
    conn.commit()
    conn.close()
