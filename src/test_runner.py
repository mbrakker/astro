# /opt/astro_bot/src/test_runner.py
# -*- coding: utf-8 -*-
import os
import sqlite3
import hashlib
import contextlib
from types import SimpleNamespace
from io import StringIO
import sys
import asyncio

def run_pipeline_test(topic_id: int, send_to_telegram: bool) -> dict:
    """
    Запускает асинхронный pipeline как функцию без subprocess.
    Подставляет test_topic_id и dry_run. После завершения откатывает изменения, если send_to_telegram=True.
    """

    # Импорт pipeline и его main(args)
    from script_pipeline import main as pipeline_main

    # Получаем тему из базы
    conn = sqlite3.connect("/opt/astro_bot/history/content_topics.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return {
            "stdout": "",
            "stderr": f"❌ Тема с id={topic_id} не найдена.",
            "returncode": 1
        }

    topic = dict(row)
    original_status = topic["status"]
    original_published_at = topic["published_at"]
    original_updated_at = topic["updated_at"]
    theme = topic.get("theme", "") or ""
    text_key = f"{theme}{topic.get('type', '')}"
    text_hash = hashlib.md5(text_key.encode("utf-8")).hexdigest()

    # Создание объекта аргументов
    args = SimpleNamespace(
        test_topic_id=topic_id,
        dry_run=not send_to_telegram,
        list_types=False
    )

    # Перехват stdout/stderr
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()

    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            asyncio.run(pipeline_main(args))
        returncode = 0
    except Exception as e:
        return {
            "stdout": stdout_buffer.getvalue(),
            "stderr": f"{stderr_buffer.getvalue()}\n❌ Ошибка выполнения: {e}",
            "returncode": 1
        }

    stdout = stdout_buffer.getvalue()
    stderr = stderr_buffer.getvalue()

    # Проверка изображения
    image_path = None
    for line in stdout.splitlines():
        if "🖼" in line:
            potential_path = line.split("🖼", 1)[-1].strip()
            if os.path.exists(potential_path):
                image_path = potential_path
                break

    # Откат изменений, если публикация была реальной
    if send_to_telegram:
        try:
            conn_p = sqlite3.connect("/opt/astro_bot/history/posts.db")
            cur_p = conn_p.cursor()
            cur_p.execute("DELETE FROM posts WHERE text_hash = ?", (text_hash,))
            conn_p.commit()
            conn_p.close()

            conn = sqlite3.connect("/opt/astro_bot/history/content_topics.db")
            cur = conn.cursor()
            cur.execute("""
                UPDATE topics
                SET status = ?, published_at = ?, updated_at = ?
                WHERE id = ?
            """, (original_status, original_published_at, original_updated_at, topic_id))
            conn.commit()
            conn.close()
        except Exception as e:
            stderr += f"\n⚠️ Ошибка при откате данных: {e}"

    return {
        "stdout": stdout,
        "stderr": stderr,
        "returncode": returncode,
        "image_path": image_path
    }
