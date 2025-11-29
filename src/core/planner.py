# src/core/planner.py

from datetime import datetime, timedelta
import pandas as pd

def _is_unscheduled(val) -> bool:
    """Считать тему незапланированной, если дата NULL или пустая строка."""
    return (val is None) or (str(val).strip() == "")

def auto_schedule(topics: list[dict], rules: list[dict]) -> list[dict]:
    """
    Автопланирование тем по заданным правилам.
    Возвращает [{"id": <topic_id>, "scheduled_for": "YYYY-MM-DD"}, ...]
    """
    results = []
    today = datetime.utcnow().date()

    for rule in rules:
        type_ = rule.get("type")
        scope = rule.get("scope", "main")
        mode  = rule.get("mode")
        value = rule.get("value")

        if not type_ or not mode:
            continue

        # Берём темы нужного типа/канала без даты (NULL или '')
        eligible = [
            t for t in topics
            if t.get("type") == type_
            and t.get("channel_scope") == scope
            and _is_unscheduled(t.get("scheduled_for"))
        ]

        if not eligible:
            continue

        # Приоритет: выше — раньше планируем
        eligible = sorted(eligible, key=lambda t: (t.get("priority") or 0), reverse=True)

        if mode == "interval":
            # value: int (каждые N дней)
            try:
                step = int(value)
            except Exception:
                step = None
            if not step or step < 1:
                continue

            next_date = today
            for topic in eligible:
                results.append({"id": topic["id"], "scheduled_for": str(next_date)})
                next_date += timedelta(days=step)

        elif mode == "weekdays":
            # value: список полных англ. названий дней, напр. ["Monday","Friday"]
            allowed = set(map(str, value or []))
            if not allowed:
                continue

            for topic in eligible:
                # Ищем ближайший подходящий день (не дальше 90 дней)
                for offset in range(1, 90):  # с завтрашнего дня
                    trial = today + timedelta(days=offset)
                    if trial.strftime("%A") in allowed:
                        results.append({"id": topic["id"], "scheduled_for": str(trial)})
                        break

        elif mode == "daily":
            # Кладём последовательно по дням (начиная с сегодня)
            next_date = today
            for topic in eligible:
                results.append({"id": topic["id"], "scheduled_for": str(next_date)})
                next_date += timedelta(days=1)

        # иные режимы при необходимости добавим позже

    return results

def fix_schedule() -> list[dict]:
    # Заглушка — сюда можно добавить анти-дубли/лимиты при необходимости
    return []
