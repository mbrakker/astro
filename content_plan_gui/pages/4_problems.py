# content_plan_gui/pages/4_problems.py

import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

# Пути
DB_PATH = "/opt/astro_bot/history/content_topics.db"
RULES_PATH = "/opt/astro_bot/config/publish_rules.yaml"

# Загрузка модулей
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
import sys
sys.path.append(SRC_PATH)
from core import rule_loader

# --- Важно: грузим "сегодня" в UTC, как в ядре/визуализаторе ---
def _utc_today():
    return datetime.utcnow().date()

# Загрузка тем из SQLite
def load_topics():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, theme, scheduled_for, status, target_sign, channel_scope AS scope
        FROM topics
        WHERE status IN ('pending', 'scheduled')
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Подготовка
topics = load_topics()
rules_data = rule_loader.load_rules_full()
rules = rules_data.get("rules", [])
min_posts = rules_data.get("min_posts_per_day", 1)
max_posts = rules_data.get("max_posts_per_day", 4)

# ⬅️ external types
_topic_sources_map = rules_data.get("topic_sources", {}) or {}
_external_types = {k for k, v in _topic_sources_map.items() if str(v).lower() == "external"}

# Группировка по дате и каналу
def group_by_day_scope(topics):
    result = defaultdict(lambda: defaultdict(list))  # result[scope][date] = [topics]
    for t in topics:
        date = t.get("scheduled_for")
        if not date:
            continue
        scope = t.get("scope", "main")
        if scope == "zodiac":
            key = (date, t.get("target_sign", "").lower())
            result[scope][key].append(t)
        else:
            result[scope][date].append(t)
    return result


grouped = group_by_day_scope(topics)

st.set_page_config(page_title="Проблемы публикации", layout="wide")

st.markdown(f"""
**🧮 Текущие лимиты публикаций: Минимум в день: **{min_posts}** - Максимум в день: **{max_posts}**
""")

st.title("🚨 Проблемы публикаций")

# 🔧 Горизонт проверки
horizon_days = st.slider("Горизонт проверки (дней вперёд)", min_value=7, max_value=100, value=14)
today = datetime.utcnow().date()
date_range = [today + timedelta(days=i) for i in range(horizon_days)]

# === 1. Дубликаты ===
with st.expander("📛 Дубликаты тем (по type + theme + дата + scope [+ target_sign для zodiac])"):
    seen_keys = set()
    duplicates = []

    for t in topics:
        theme_norm = t.get("theme", "").strip().lower()
        scope = t.get("scope", "main")
        date = t.get("scheduled_for")

        raw_sign = t.get("target_sign", "")
        normalized_sign = raw_sign.strip().lower() if raw_sign else ""

        key = (
            t.get("type", "").lower(),
            theme_norm,
            date,
            scope,
            normalized_sign if scope == "zodiac" else None
        )

        if key in seen_keys:
            duplicates.append({
                "type": t.get("type", ""),
                "theme": t.get("theme", ""),
                "date": date,
                "scope": scope,
                "target_sign": raw_sign  # исходный, без преобразования
            })
        else:
            seen_keys.add(key)

    if duplicates:
        st.error(f"Найдено дубликатов: {len(duplicates)}")
        st.dataframe(pd.DataFrame(duplicates))
    else:
        st.success("✅ Дубликатов не найдено")

    # 🔧 Новый блок управления дубликатами
    st.markdown("### 🛠 Исправление дубликатов")
    fix_action = st.radio("Что делать с дубликатами?", ["распределить", "удалить"], horizontal=True)

    if st.button("🧹 Исправить дубликаты"):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        today = datetime.utcnow().date()

        for dup in duplicates:
            dup_type = dup["type"]
            scope = dup["scope"]
            theme = dup["theme"]
            date = dup["date"]
            target_sign = dup.get("target_sign")
   
             # Найдём все дублирующие записи по type+theme+date+scope(+sign)
            cur.execute("""
                SELECT id FROM topics
                WHERE type = ? AND theme = ? AND scheduled_for = ? AND channel_scope = ?
                AND (target_sign = ? OR ? IS NULL)
                ORDER BY id
            """, (dup_type, theme, date, scope, target_sign, target_sign))
            rows = cur.fetchall()

            if not rows or len(rows) <= 1:
                continue  # нет дублей

            # Оставим первую, остальные обработаем
            ids_to_handle = [r[0] for r in rows][1:]

            if fix_action == "удалить":
                cur.executemany("DELETE FROM topics WHERE id = ?", [(i,) for i in ids_to_handle])
  
            elif fix_action == "распределить":
                # Загружаем правила
                rule = next((r for r in rules if r["type"] == dup_type and r["scope"] == scope), None)
                if not rule:
                    continue  # нет правил

                mode = rule.get("mode")
                value = rule.get("value")

                # Пробуем найти дату, куда можно перенести
                for topic_id in ids_to_handle:
                    offset = 1
                    while offset < 90:  # максимум 90 дней вперёд
                        new_date = datetime.strptime(date, "%Y-%m-%d").date() + timedelta(days=offset)
                        iso = new_date.isoformat()
                        weekday = calendar.day_name[new_date.weekday()]
                        allow = False

                        if mode == "daily":
                            allow = True
                        elif mode == "interval" and (offset % int(value)) == 0:
                            allow = True
                        elif mode == "weekdays" and weekday in value:
                            allow = True

                        if not allow:
                            offset += 1
                            continue

                        # Проверим, занята ли дата
                        if scope == "zodiac":
                            cur.execute("""
                                SELECT COUNT(*) FROM topics WHERE scheduled_for = ? AND channel_scope = 'zodiac' AND target_sign = ?
                            """, (iso, target_sign))
                            count = cur.fetchone()[0]
                            if count == 0:
                                cur.execute("UPDATE topics SET scheduled_for = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (iso, topic_id))
                                break
                        else:
                            cur.execute("""
                                SELECT COUNT(*) FROM topics WHERE scheduled_for = ? AND channel_scope = 'main'
                            """, (iso,))
                            count = cur.fetchone()[0]
                            if count < max_posts:
                                cur.execute("UPDATE topics SET scheduled_for = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (iso, topic_id))
                                break
                        offset += 1

        conn.commit()
        conn.close()
        st.success("✅ Дубликаты успешно обработаны. Перезапусти вкладку для обновления.")


# === 2. Перегруз по max_posts_per_day ===
with st.expander("🧨 Перегруз по каналам"):
    overloads = []

    zodiac_seen = set()  # чтобы не считать один день дважды
    main_counts = defaultdict(int)

    for t in topics:
        date = t.get("scheduled_for")
        scope = t.get("scope")
        if not date or not scope:
            continue

        if scope == "zodiac":
            zodiac_seen.add(date)  # любой target_sign = 1 публикация
        elif scope == "main":
            main_counts[date] += 1

    # Проверка перегруза
    for date in zodiac_seen:
        if max_posts and 1 > max_posts:
            overloads.append({
                "scope": "zodiac",
                "date": date,
                "count": 1
            })

    for date, count in main_counts.items():
        if count > max_posts:
            overloads.append({
                "scope": "main",
                "date": date,
                "count": count
            })

    if overloads:
        st.error(f"Найдено дней с перегрузом: {len(overloads)}")
        st.dataframe(pd.DataFrame(overloads))
    else:
        st.success("✅ Перегруза не обнаружено")

    # 🔧 Управление перегрузом
    st.markdown("### 🛠 Исправление перегруза")
    overload_action = st.radio("Что делать с перегрузом?", ["распределить", "удалить"], horizontal=True)

    if st.button("🧹 Исправить перегруз"):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        for row in overloads:
            scope = row["scope"]
            date = row["date"]

            if scope == "main":
                cur.execute("""
                    SELECT id, type FROM topics
                    WHERE scheduled_for = ? AND channel_scope = 'main'
                    ORDER BY id
                """, (date,))
                rows = cur.fetchall()
                if len(rows) <= max_posts:
                    continue

                keep = rows[:max_posts]
                extras = rows[max_posts:]

                if overload_action == "удалить":
                    cur.executemany("DELETE FROM topics WHERE id = ?", [(r[0],) for r in extras])

                elif overload_action == "распределить":
                    for topic_id, topic_type in extras:
                        rule = next((r for r in rules if r["type"] == topic_type and r["scope"] == "main"), None)
                        if not rule:
                            continue
                        mode = rule["mode"]
                        value = rule["value"]
                        offset = 1
                        while offset < 90:
                            new_date = datetime.strptime(date, "%Y-%m-%d").date() + timedelta(days=offset)
                            iso = new_date.isoformat()
                            weekday = calendar.day_name[new_date.weekday()]
                            allow = (
                                mode == "daily"
                                or (mode == "interval" and offset % int(value) == 0)
                                or (mode == "weekdays" and weekday in value)
                            )
                            if not allow:
                                offset += 1
                                continue
                            cur.execute("""
                                SELECT COUNT(*) FROM topics
                                WHERE scheduled_for = ? AND channel_scope = 'main'
                            """, (iso,))
                            count = cur.fetchone()[0]
                            if count < max_posts:
                                cur.execute("UPDATE topics SET scheduled_for = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (iso, topic_id))
                                break
                            offset += 1

            elif scope == "zodiac":
                cur.execute("""
                    SELECT id, type, target_sign FROM topics
                    WHERE scheduled_for = ? AND channel_scope = 'zodiac'
                    ORDER BY id
                """, (date,))
                zodiac_topics = cur.fetchall()
                seen_signs = set()
                to_delete = []
                to_move = []

                for topic_id, topic_type, sign in zodiac_topics:
                    if sign in seen_signs:
                        if overload_action == "удалить":
                            to_delete.append((topic_id,))
                        else:
                            to_move.append((topic_id, topic_type, sign))
                    else:
                        seen_signs.add(sign)

                if overload_action == "удалить":
                    cur.executemany("DELETE FROM topics WHERE id = ?", to_delete)

                elif overload_action == "распределить":
                    for topic_id, topic_type, sign in to_move:
                        rule = next((r for r in rules if r["type"] == topic_type and r["scope"] == "zodiac"), None)
                        if not rule:
                            continue
                        mode = rule["mode"]
                        value = rule["value"]
                        offset = 1
                        while offset < 90:
                            new_date = datetime.strptime(date, "%Y-%m-%d").date() + timedelta(days=offset)
                            iso = new_date.isoformat()
                            weekday = calendar.day_name[new_date.weekday()]
                            allow = (
                                mode == "daily"
                                or (mode == "interval" and offset % int(value) == 0)
                                or (mode == "weekdays" and weekday in value)
                            )
                            if not allow:
                                offset += 1
                                continue
                            cur.execute("""
                                SELECT COUNT(*) FROM topics
                                WHERE scheduled_for = ? AND channel_scope = 'zodiac' AND target_sign = ?
                            """, (iso, sign))
                            count = cur.fetchone()[0]
                            if count == 0:
                                cur.execute("UPDATE topics SET scheduled_for = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (iso, topic_id))
                                break
                            offset += 1

        conn.commit()
        conn.close()
        st.success("✅ Перегруз успешно обработан. Обнови вкладку для проверки.")


# === 3. Недогруз по min_posts_per_day ===
with st.expander("📉 Недогруз по каналам"):
    underloads = []

    zodiac_seen = set()
    main_counts = defaultdict(int)

    for t in topics:
        date = t.get("scheduled_for")
        scope = t.get("scope")
        if not date or not scope:
            continue

        if scope == "zodiac":
            zodiac_seen.add(date)
        elif scope == "main":
            main_counts[date] += 1

    # горизонт проверки
    today = datetime.utcnow().date()
    for d in date_range:
        d = d.isoformat()

        if d in zodiac_seen:
            if 1 < min_posts:
                underloads.append({"scope": "zodiac", "date": d, "count": 1})
        else:
            underloads.append({"scope": "zodiac", "date": d, "count": 0})

        if main_counts[d] < min_posts:
            underloads.append({"scope": "main", "date": d, "count": main_counts[d]})

    if underloads:
        st.warning(f"Найдено дней с недогрузом: {len(underloads)}")
        st.dataframe(pd.DataFrame(underloads))
    else:
        st.success("✅ Недогруза не обнаружено")



# === 4. Отсутствуют публикации на горизонте планироования ===
with st.expander("📭 Пустые дни (нет ни одной темы)"):
    today = datetime.utcnow().date()
    empty_days = {"main": [], "zodiac": []}
    dates = date_range

    for scope in ["main", "zodiac"]:
        scheduled = grouped.get(scope, {})
        for d in dates:
            ds = d.isoformat()

            if scope == "main":
                if ds not in scheduled or not scheduled[ds]:
                    empty_days[scope].append(ds)

            elif scope == "zodiac":
                has_any = any(k[0] == ds for k in scheduled.keys())  # ⬅️ fix
                if not has_any:
                    empty_days[scope].append(ds)

    for scope in ["main", "zodiac"]:
        if empty_days[scope]:
            st.warning(f"В канале `{scope}` нет публикаций в дни: {', '.join(empty_days[scope])}")
        else:
            st.success(f"✅ В канале `{scope}` публикации есть на все 14 дней")

# === 5. Несоответствие правилам публикации ===
with st.expander("⚠️ Несоответствие правилам publish_rules.yaml", expanded=True):
    problems = []

    # Накапливаем пропуски только для DAILY и scope != 'zodiac'
    # ключ: (rtype, scope) -> [YYYY-MM-DD, ...]
    missing_daily = {}

    for rule in rules:
        scope = rule.get("scope", "main")
        rtype = rule.get("type")
        mode = rule.get("mode")
        value = rule.get("value")

        if not rtype or not mode:
            continue

        # 1️⃣ ПРОВЕРКА: тема должна быть, но её нет
        for date in date_range:
            delta = (date - today).days
            weekday = calendar.day_name[date.weekday()]
            iso = date.isoformat()

            should_publish = (
                mode == "daily"
                or (mode == "interval" and isinstance(value, int) and value > 0 and delta % int(value) == 0)
                or (mode == "weekdays" and (value or []) and weekday in value)
            )
            if not should_publish:
                continue

            matches = [
                t
                for t in topics
                if t["type"] == rtype and t["scope"] == scope and t.get("scheduled_for") == iso
            ]
            if not matches:
                # ⬅️ skip external (по topic_sources)
                if rtype in _external_types:
                    continue

                problems.append(
                    {
                        "scope": scope,
                        "date": iso,
                        "type": rtype,
                        "expected": f"{mode}: {value}",
                        "status": "❌ тема не запланирована",
                    }
                )
                # Копим пропуски только для DAILY и не-zodiac
                if mode == "daily" and scope != "zodiac":
                    # ⬅️ skip external в накоплении missing_daily
                    if rtype not in _external_types:
                        missing_daily.setdefault((rtype, scope), []).append(iso)

        # 2️⃣ ПРОВЕРКА: тема запланирована, но не должна быть
        for t in topics:
            if t["type"] != rtype or t["scope"] != scope:
                continue

            t_date = t.get("scheduled_for")
            if not t_date:
                continue

            try:
                t_date_obj = datetime.strptime(t_date, "%Y-%m-%d").date()
            except ValueError:
                continue

            delta = (t_date_obj - today).days
            if delta < 0 or delta >= horizon_days:
                continue  # вне диапазона анализа

            weekday = calendar.day_name[t_date_obj.weekday()]
            allowed = (
                mode == "daily"
                or (mode == "interval" and isinstance(value, int) and value > 0 and delta % int(value) == 0)
                or (mode == "weekdays" and (value or []) and weekday in value)
            )

            if not allowed:
                problems.append(
                    {
                        "scope": scope,
                        "date": t_date,
                        "type": rtype,
                        "expected": f"{mode}: {value}",
                        "status": "❌ тема запланирована в недопустимый день",
                    }
                )

    # 🧾 Вывод результата
    if problems:
        st.error(f"Несоответствий найдено: {len(problems)}")
        st.dataframe(pd.DataFrame(problems))
    else:
        st.success("✅ Все публикации соответствуют правилам")

    # ➕ Кнопка: автодобавление отсутствующих DAILY для scope != 'zodiac'
    if missing_daily:
        if st.button("➕ Добавить отсутствующие публикации для daily"):
            inserted = 0
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            for (rtype, scope), dates in missing_daily.items():
                for iso in dates:
                    # Перестраховка: нет ли уже записи в БД?
                    cur.execute(
                        """
                        SELECT 1 FROM topics
                        WHERE type = ? AND channel_scope = ? AND scheduled_for = ?
                        """,
                        (rtype, scope, iso),
                    )
                    if cur.fetchone():
                        continue

                    # Вставка минимально необходимого набора полей
                    cur.execute(
                        """
                        INSERT INTO topics
                            (type, theme, channel_scope, status, scheduled_for, created_at, updated_at)
                        VALUES
                            (?,    ?,     ?,            'pending', ?,            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (rtype, f"auto:{rtype}:{iso}", scope, iso),
                    )
                    inserted += 1

            conn.commit()
            conn.close()

            if inserted:
                st.success(
                    f"✅ Добавлено недостающих daily-публикаций: {inserted}. Обнови страницу для пересчёта."
                )
            else:
                st.info("Нет пропусков для добавления или они уже закрыты.")

# (СОХРАНЕНО) Кнопка «🛠 Исправить недопустимые дни» — перенос тем на валидные даты
if st.button("🛠 Исправить недопустимые дни"):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    changes = 0
    iteration = 0
    max_iterations = 1000

    # Словарь правил: (type, scope) → {mode, value}
    rule_map = {}
    for r in rules:
        key = (r.get("type"), r.get("scope"))
        if not key[0] or not key[1]:
            continue
        rule_map[key] = {"mode": r.get("mode"), "value": r.get("value")}

    while iteration < max_iterations:
        iteration += 1

        cur.execute("SELECT * FROM topics WHERE scheduled_for IS NOT NULL")
        rows = cur.fetchall()
        all_topics = [dict(r) for r in rows]

        # Собираем занятые даты/ключи
        occupied = set()
        for t in all_topics:
            scope = t["channel_scope"]
            key = (scope, t["scheduled_for"], t["type"])
            if scope == "zodiac":
                key += (t.get("target_sign"),)
            occupied.add(key)

        # Находим темы, стоящие в "неразрешённые" дни
        wrong_topics = []
        for t in all_topics:
            scope = t["channel_scope"]
            rkey = (t["type"], scope)
            if rkey not in rule_map:
                continue

            mode = rule_map[rkey]["mode"]
            value = rule_map[rkey]["value"]
            t_date = t.get("scheduled_for")
            if not t_date:
                continue

            try:
                scheduled = datetime.strptime(t_date, "%Y-%m-%d").date()
            except Exception:
                continue

            delta = (scheduled - today).days
            weekday = calendar.day_name[scheduled.weekday()]

            # Нормализация значений для weekdays
            if mode == "weekdays":
                if isinstance(value, str):
                    value = [value]
                value = [v.strip().capitalize() for v in (value or [])]

            allowed = (
                mode == "daily"
                or (mode == "interval" and isinstance(value, int) and value > 0 and delta % int(value) == 0)
                or (mode == "weekdays" and value and weekday in value)
            )

            if not allowed:
                wrong_topics.append(t)

        if not wrong_topics:
            break

        # Перенос на ближайшую допустимую дату без конфликтов
        for t in wrong_topics:
            scope = t["channel_scope"]
            rkey = (t["type"], scope)
            mode = rule_map[rkey]["mode"]
            value = rule_map[rkey]["value"]

            # Нормализуем value для weekdays
            if mode == "weekdays":
                if isinstance(value, str):
                    value = [value]
                value = [v.strip().capitalize() for v in (value or [])]

            try:
                original = datetime.strptime(t["scheduled_for"], "%Y-%m-%d").date()
            except Exception:
                continue

            for offset in range(1, 365):
                new_date = original + timedelta(days=offset)
                delta = (new_date - today).days
                weekday = calendar.day_name[new_date.weekday()]
                iso = new_date.isoformat()

                allowed = (
                    mode == "daily"
                    or (mode == "interval" and isinstance(value, int) and value > 0 and delta % int(value) == 0)
                    or (mode == "weekdays" and value and weekday in value)
                )
                if not allowed:
                    continue

                key = (scope, iso, t["type"])
                if scope == "zodiac":
                    key += (t.get("target_sign"),)
                if key in occupied:
                    continue

                cur.execute(
                    """
                    UPDATE topics
                    SET scheduled_for = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (iso, t["id"]),
                )
                occupied.add(key)
                changes += 1
                break

    conn.commit()
    conn.close()

    if changes > 0:
        st.success(f"✅ Перенесено {changes} тем на корректные даты за {iteration} итераций.")
    else:
        st.info("✅ Все темы уже соответствуют правилам.")

# === 6. Корректность target_sign для zodiac ===

with st.expander("⚠️ Темы с некорректным или пустым target_sign в канале zodiac"):
    VALID_SIGNS = {
        "овен", "телец", "близнецы", "рак", "лев", "дева",
        "весы", "скорпион", "стрелец", "козерог", "водолей", "рыбы"
    }

    issues = []

    for t in topics:
        if t.get("scope") != "zodiac":
            continue

        raw_sign = t.get("target_sign")
        normalized = str(raw_sign).strip().lower() if raw_sign else ""

        if normalized not in VALID_SIGNS:
            issues.append({
                "id": t.get("id"),
                "type": t.get("type"),
                "theme": t.get("theme"),
                "target_sign": raw_sign or "",
                "scheduled_for": t.get("scheduled_for"),
                "status": t.get("status")
            })

    if issues:
        st.warning(f"Найдено тем с отсутствующим или некорректным target_sign: {len(issues)}")
        st.dataframe(pd.DataFrame(issues))
    else:
        st.success("✅ Все темы в канале zodiac содержат допустимый target_sign")

with st.expander("❗ Темы в канале main без темы (theme)"):
    missing_themes = []

    for t in topics:
        if t.get("scope") != "main":
            continue

        theme = t.get("theme")
        if not theme or not str(theme).strip():
            missing_themes.append({
                "id": t.get("id"),
                "type": t.get("type"),
                "scheduled_for": t.get("scheduled_for"),
                "status": t.get("status")
            })

    if missing_themes:
        st.warning(f"Найдено тем в канале main без заполненного theme: {len(missing_themes)}")
        st.dataframe(pd.DataFrame(missing_themes))
    else:
        st.success("✅ Все темы в канале main содержат тему (theme)")

with st.expander("🧾 Проверка корректности сгенерированных тем"):
    problems = []

    # Извлекаем только правила с topic_source = generated
    generated_rules = [r for r in rules if r.get("topic_source") == "generated"]

    for rule in generated_rules:
        rtype = rule["type"]
        scope = rule.get("scope", "main")

        for t in topics:
            if t["type"] != rtype or t["scope"] != scope:
                continue

            theme = t.get("theme", "").strip()
            word_count = len(theme.split())

            if word_count <= 3:
                problems.append({
                    "id": t.get("id"),
                    "type": rtype,
                    "scope": scope,
                    "theme": theme,
                    "words": word_count,
                    "scheduled_for": t.get("scheduled_for"),
                    "status": "⚠️ слишком короткая тема"
                })

    if problems:
        st.warning(f"Тем с подозрительно короткой темой: {len(problems)}")
        st.dataframe(pd.DataFrame(problems))
    else:
        st.success("✅ Все сгенерированные темы выглядят корректно")
