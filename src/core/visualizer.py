# src/core/visualizer.py

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "/opt/astro_bot/history/content_topics.db"

def get_heatmap_data(days: int = 30, group_by: str = "channel_scope") -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT scheduled_for, channel_scope, type
        FROM topics
        WHERE scheduled_for IS NOT NULL
        AND status IN ('pending', 'scheduled')
    """, conn)

    if df.empty:
        return pd.DataFrame()

    df["scheduled_for"] = pd.to_datetime(df["scheduled_for"]).dt.date
    df = df[df["scheduled_for"] <= datetime.utcnow().date() + timedelta(days=days)]

    df["count"] = 1
    grouped = df.groupby([group_by, "scheduled_for"]).count().reset_index()
    pivot = grouped.pivot(index=group_by, columns="scheduled_for", values="count").fillna(0).astype(int)

    return pivot

def get_upcoming_posts(days: int = 30) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    today = datetime.utcnow().date()
    until = today + timedelta(days=days)

    df = pd.read_sql_query("""
        SELECT id, type, theme, scheduled_for, status, channel_scope, target_sign
        FROM topics
        WHERE scheduled_for BETWEEN ? AND ?
        ORDER BY scheduled_for ASC
    """, conn, params=(str(today), str(until)))
    return df
