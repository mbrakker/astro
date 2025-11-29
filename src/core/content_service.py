# src/core/content_service.py

import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "/opt/astro_bot/history/content_topics.db"

def get_summary_by_type():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT type, status, COUNT(*) as count
        FROM topics
        GROUP BY type, status
        ORDER BY type
    """, conn)
    pivot = df.pivot(index='type', columns='status', values='count').fillna(0).astype(int)
    return pivot.reset_index()

def get_all_topics(mode="dataframe"):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query("SELECT * FROM topics ORDER BY updated_at DESC", conn)

    if mode == "dataframe":
        return df
    elif mode == "types":
        return sorted(df["type"].dropna().unique().tolist())
    elif mode == "statuses":
        return sorted(df["status"].dropna().unique().tolist())

def update_topics(edited_df: pd.DataFrame) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    updated_rows = 0
    for _, row in edited_df.iterrows():
        cur.execute("""
            UPDATE topics SET
                type = ?, subtype = ?, theme = ?, context = ?, 
                channel_scope = ?, target_sign = ?, priority = ?, 
                scheduled_for = ?, status = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (
            row["type"], row.get("subtype"), row["theme"], row.get("context"),
            row["channel_scope"], row.get("target_sign"), row.get("priority"),
            row.get("scheduled_for"), row["status"], row.get("notes"),
            datetime.utcnow(), row["id"]
        ))
        updated_rows += 1
    conn.commit()
    return updated_rows

def add_new_topic(topic_type, theme, channel_scope) -> int:
    now = datetime.utcnow()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO topics (type, theme, channel_scope, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (topic_type, theme, channel_scope, "pending", now, now))
    conn.commit()
    return cur.lastrowid

def get_unplanned_topics():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM topics
        WHERE status = 'pending' AND scheduled_for IS NULL
    """)
    return [dict(row) for row in cur.fetchall()]

def get_today_schedule():
    conn = sqlite3.connect(DB_PATH)
    today = datetime.utcnow().date().isoformat()
    df = pd.read_sql_query("""
        SELECT id, type, theme, channel_scope, status
        FROM topics
        WHERE scheduled_for = ?
        ORDER BY channel_scope
    """, conn, params=(today,))
    return df

def update_schedule_batch(schedule: list[dict]) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    count = 0
    for item in schedule:
        cur.execute("""
            UPDATE topics
            SET scheduled_for = ?, updated_at = ?
            WHERE id = ?
        """, (item["scheduled_for"], datetime.utcnow(), item["id"]))
        count += 1
    conn.commit()
    return count

def get_pending_topics_without_schedule() -> list[dict]:
    """
    Возвращает все темы со статусом 'pending', у которых не задан scheduled_for.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM topics
        WHERE status = 'pending' AND (scheduled_for IS NULL OR scheduled_for = '')
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
