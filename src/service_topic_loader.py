#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime
import argparse
import os
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


DB_PATH = "/opt/astro_bot/history/content_topics.db"

def get_connection():
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def get_pending_topic(topic_type, subtype=None, channel_scope="main", target_sign=None):
    """
    Вернёт первую «pending» тему по типу (и подтипу, если указано),
    с учётом scheduled_for (<= сегодня или NULL).
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
    SELECT *
      FROM topics
     WHERE type = ?
       AND status = 'pending'
       AND (scheduled_for IS NULL OR scheduled_for <= DATE('now'))
       AND channel_scope = ?
    """
    params = [topic_type, channel_scope]

    if subtype:
        sql += " AND subtype = ?"
        params.append(subtype)
    if target_sign:
        sql += " AND (target_sign IS NULL OR target_sign = ?)"
        params.append(target_sign)

    sql += """
     ORDER BY
       scheduled_for IS NULL,           -- темы с датой первыми
       scheduled_for ASC,
       priority DESC,
       created_at ASC
     LIMIT 1
    """

    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None

def update_topic_status(topic_id, status, note=None):
    """
    Помечает тему статусом ('published','skipped','error'),
    обновляет published_at (для 'published') и updated_at,
    сохраняет опциональную заметку.
    """
    now = datetime.now().isoformat(sep=' ')
    conn = get_connection()
    cur = conn.cursor()

    sql = """
    UPDATE topics
       SET status = ?,
           updated_at = ?,
           published_at = CASE WHEN ? = 'published' THEN ? ELSE published_at END
    """
    params = [status, now, status, now]

    if note:
        sql += ", notes = COALESCE(notes, '') || ?"
        params.append(f"\n{now} — {note}")

    sql += " WHERE id = ?"
    params.append(topic_id)

    cur.execute(sql, params)
    conn.commit()
    conn.close()

def get_pending_topics(topic_type, **filters):
    """
    Вернёт список всех тем в статусе pending по типу.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    sql = """
    SELECT * FROM topics
     WHERE type = ?
       AND status = 'pending'
       AND (scheduled_for IS NULL OR scheduled_for <= DATE('now'))
    """
    params = [topic_type]
    # сюда можно добавить фильтрацию по subtype, channel_scope и т.д.
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_topic_published(topic_id):
    """Синоним update_topic_status(id,'published')."""
    update_topic_status(topic_id, 'published')

def main():
    parser = argparse.ArgumentParser(
        description="Topic Loader for Scarlet Luna pipeline"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Получить тему
    getp = sub.add_parser("get", help="Get next pending topic")
    getp.add_argument("type", help="Topic type, e.g. confession, astro_basics")
    getp.add_argument("--subtype", help="Optional subtype filter")
    getp.add_argument("--channel", default="main", help="Channel scope (main/zodiac/all)")
    getp.add_argument("--sign", help="Optional target_sign filter")

    # Пометить как опубликованную
    pub = sub.add_parser("publish", help="Mark topic as published")
    pub.add_argument("id", type=int, help="Topic ID to mark as published")

    # Пометить как пропущенную
    skip = sub.add_parser("skip", help="Mark topic as skipped")
    skip.add_argument("id", type=int, help="Topic ID to mark as skipped")
    skip.add_argument("--note", help="Optional note about skip")

    # Пометить как ошибочную
    err = sub.add_parser("error", help="Mark topic as error")
    err.add_argument("id", type=int, help="Topic ID to mark as error")
    err.add_argument("--note", help="Optional error note")

    args = parser.parse_args()

    if args.cmd == "get":
        topic = get_pending_topic(
            args.type,
            subtype=args.subtype,
            channel_scope=args.channel,
            target_sign=args.sign
        )
        if topic:
            print(json.dumps(topic, ensure_ascii=False, indent=2))
        else:
            print("No pending topics found.")
    elif args.cmd == "publish":
        update_topic_status(args.id, "published")
        print(f"Topic {args.id} marked as published.")
    elif args.cmd == "skip":
        update_topic_status(args.id, "skipped", note=args.note)
        print(f"Topic {args.id} marked as skipped.")
    elif args.cmd == "error":
        update_topic_status(args.id, "error", note=args.note)
        print(f"Topic {args.id} marked as error.")

def get_all_scheduled_topics(target_date: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM topics
        WHERE scheduled_for = ? AND status IN ('pending', 'scheduled')
        ORDER BY priority DESC, created_at ASC
    """, (target_date,))
    topics = [dict(row) for row in cur.fetchall()]
    conn.close()
    return topics

def get_topic_by_id(topic_id: int) -> dict | None:
    import sqlite3
    conn = sqlite3.connect("/opt/astro_bot/history/content_topics.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


if __name__ == "__main__":
    main()
