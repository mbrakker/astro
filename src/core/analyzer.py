# src/core/analyzer.py

import sqlite3
import pandas as pd

DB_PATH = "/opt/astro_bot/history/content_topics.db"

def find_duplicates() -> pd.DataFrame:
    """Темы с одинаковыми type + theme + scheduled_for"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT id, type, theme, scheduled_for, COUNT(*) as count
        FROM topics
        WHERE scheduled_for IS NOT NULL
        GROUP BY type, theme, scheduled_for
        HAVING COUNT(*) > 1
    """, conn)
    return df

def find_channel_overload(limit: int = 3) -> pd.DataFrame:
    """Дни, где на канал запланировано больше N постов"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT channel_scope, scheduled_for, COUNT(*) as count
        FROM topics
        WHERE scheduled_for IS NOT NULL
        GROUP BY channel_scope, scheduled_for
        HAVING count > ?
    """, conn, params=(limit,))
    return df

def find_missing_days(days_ahead: int = 14) -> pd.DataFrame:
    """Каналы, у которых нет постов на ближайшие дни"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT channel_scope, scheduled_for
        FROM topics
        WHERE scheduled_for IS NOT NULL
    """, conn)

    future = pd.date_range(start=pd.Timestamp.today().normalize(), periods=days_ahead)
    all_channels = df["channel_scope"].unique()

    rows = []
    for ch in all_channels:
        ch_dates = df[df["channel_scope"] == ch]["scheduled_for"]
        for day in future:
            if day.date().isoformat() not in set(ch_dates):
                rows.append({"channel_scope": ch, "missing_date": day.date()})

    return pd.DataFrame(rows)
