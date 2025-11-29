# content_plan_gui/content_plan.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from collections import defaultdict
import pandas as pd
from datetime import datetime, timedelta
import calendar

import streamlit as st
from core.visualizer import get_heatmap_data, get_upcoming_posts
from core.content_types import CONTENT_TYPES  # ✅ Новый импорт

st.set_page_config(page_title="Контент-план", layout="wide")
st.title("📊 Контент-план: вперед на 90 дней")

col1, col2 = st.columns(2)
with col1:
    horizon = st.selectbox("Горизонт планирования", [7, 30, 90], index=1)
with col2:
    group_by = st.selectbox("Группировка", ["channel_scope", "type"], index=0)

# 🔥 HEATMAP
st.markdown("### 🔥 Загрузка по дням")
heatmap_df = get_heatmap_data(days=horizon, group_by=group_by)

if heatmap_df.empty:
    st.info("Нет запланированных публикаций в выбранный период.")
else:
    st.dataframe(heatmap_df, use_container_width=True)

# 📅 СПИСОК ТЕМ
st.markdown("---")
st.markdown("### 📅 Запланированные публикации")

# ✅ Новый фильтр по типу
selected_type = st.selectbox("Фильтр по типу контента", ["Все"] + CONTENT_TYPES)

upcoming_df = get_upcoming_posts(days=horizon)


if selected_type != "Все":
    upcoming_df = upcoming_df[upcoming_df["type"] == selected_type]

st.dataframe(upcoming_df, use_container_width=True)

# 🕰 ДОБАВЛЕННЫЕ. НО НЕ ЗАПЛАНИРОВАННЫЕ ТЕМЫ

with st.expander("🕰 Добавленные, но не запланированные темы"):
    from core.content_service import get_all_topics, get_pending_topics_without_schedule
    from core.rule_loader import load_rules_full
    from datetime import datetime, timedelta
    import sqlite3

    all_topics = get_all_topics(mode="dataframe").to_dict(orient="records")
    unplanned = get_pending_topics_without_schedule()

    if unplanned:
        df = pd.DataFrame(unplanned)
        st.info(f"Всего тем без даты публикации: {len(df)}")
        st.dataframe(df[["type", "theme", "channel_scope", "target_sign", "status", "created_at"]], use_container_width=True)

        if st.button("📆 Запланировать"):
            # Загружаем правила
            rules_data = load_rules_full()
            rules = rules_data.get("rules", [])

            # Строим карту уже занятых дат
            occupied = set()
            for t in all_topics:
                if t.get("scheduled_for"):
                    key = (t["channel_scope"], t["scheduled_for"], t["type"])
                    if t["channel_scope"] == "zodiac":
                        key += (t["target_sign"],)
                    occupied.add(key)

            # Подготовка к планированию
            today = datetime.today().date()
            planning_horizon = 90
            conn = sqlite3.connect("/opt/astro_bot/history/content_topics.db")
            cur = conn.cursor()

            for rule in rules:
                scope = rule["scope"]
                topic_type = rule["type"]
                mode = rule["mode"]
                value = rule["value"]

                # Выбираем pending темы нужного типа и scope
                pool = [t for t in unplanned if t["type"] == topic_type and t["channel_scope"] == scope]
                if scope == "zodiac":
                    # Группируем по target_sign
                    pool_by_sign = {}
                    for t in pool:
                        sign = t.get("target_sign")
                        if sign:
                            pool_by_sign.setdefault(sign, []).append(t)

                    for sign, topics in pool_by_sign.items():
                        for day in range(planning_horizon):
                            date = today + timedelta(days=day)
                            weekday = date.strftime("%A")
                            allow = (
                                mode == "daily"
                                or (mode == "interval" and day % int(value) == 0)
                                or (mode == "weekdays" and weekday in value)
                            )
                            key = ("zodiac", date.isoformat(), topic_type, sign)
                            if allow and key not in occupied and topics:
                                t = topics.pop(0)
                                cur.execute("UPDATE topics SET scheduled_for = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (date.isoformat(), t["id"]))
                                occupied.add(key)
                            if not topics:
                                break
                else:  # main
                    for t in pool:
                        for day in range(planning_horizon):
                            date = today + timedelta(days=day)
                            weekday = date.strftime("%A")
                            allow = (
                                mode == "daily"
                                or (mode == "interval" and day % int(value) == 0)
                                or (mode == "weekdays" and weekday in value)
                            )
                            key = ("main", date.isoformat(), topic_type)
                            if allow and key not in occupied:
                                cur.execute("UPDATE topics SET scheduled_for = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (date.isoformat(), t["id"]))
                                occupied.add(key)
                                break

            conn.commit()
            conn.close()
            st.success("✅ Темы успешно распределены по датам. Обновите вкладку.")
    else:
        st.success("✅ Все темы запланированы")


# 📆 ВИЗУАЛИЗАЦИЯ КОНТЕНТ-ПЛАНА ПО ФАКТУ
st.markdown("---")
st.subheader("📆 Визуализация запланированных публикаций по дням")

# Эмодзи по типу контента
EMOJI_MAP = {
    "horoscope": "♈",
    "energy_day": "🌕",
    "zodiac_energy": "♌",
    "mystic_news": "🌌",
    "confession": "🔥",
    "astro_basics": "📘"
}

# === Визуализация по факту публикаций ===

# План по каналам и дням
# ✅ Формируем словарь {scope -> date_str -> [посты]}
plan = {"main": defaultdict(list), "zodiac": defaultdict(list)}

for _, row in upcoming_df.iterrows():
    date_str = str(pd.to_datetime(row["scheduled_for"]).date())
    scope = row["channel_scope"]
    content_type = row["type"]
    label = EMOJI_MAP.get(content_type, "🌀") + " " + content_type.replace("_", " ").title()

    if scope == "zodiac":
        sign = row.get("target_sign", "").capitalize()
        key = (date_str, content_type)
        if key not in plan[scope]:
            plan[scope][key] = set()
        plan[scope][key].add(sign)
    else:
        plan[scope][date_str].append(label)

# 📦 Постобработка Zodiac — агрегируем по дате + типу
zodiac_plan_by_date = defaultdict(list)

for (date_str, content_type), signs in plan["zodiac"].items():
    emoji = EMOJI_MAP.get(content_type, "🌀")
    label = f"{emoji} {content_type.replace('_', ' ').title()} ({len(signs)} знаков)"
    zodiac_plan_by_date[date_str].append(label)

plan["zodiac"] = zodiac_plan_by_date  # 🔄 заменяем на агрегированный


# Формируем таблицу строка = неделя, столбцы = дни
def make_week_table(scope: str, start_date: datetime.date, horizon: int = 30):
    num_weeks = (horizon + 6) // 7
    rows = []

    for w in range(num_weeks):
        week_start = start_date + timedelta(days=w * 7)
        row = {}
        for d in range(7):
            date = week_start + timedelta(days=d)
            date_str = date.strftime("%Y-%m-%d")
            label_lines = plan[scope].get(date_str, [])

            # Дата первой строкой, затем каждый пост на новой строке
            lines = [f"<b>{date.strftime('%d.%m')}</b>"] + label_lines
            cell = "<br>".join(lines)

            row[calendar.day_abbr[date.weekday()]] = cell
        row_label = f"{scope.capitalize()} (Week {w+1})"
        rows.append((row_label, row))
    return rows

today = datetime.today()
start_date = today - timedelta(days=today.weekday())

# ⬆️ Глобальный стиль ячеек
st.markdown("""
    <style>
    td {
        text-align: left !important;
        vertical-align: top !important;
        line-height: 1.5em !important;
        font-size: 15px !important;
        padding: 0.4em !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    table {
        table-layout: fixed;
        width: 100%;
        font-size: 15px;
        border-collapse: collapse;
    }
    th, td {
        word-wrap: break-word;
        vertical-align: top;
        padding: 0.4em;
    }
    th:nth-child(1), td:nth-child(1) {
        width: 17ch;
        max-width: 17ch;
    }
    th:nth-child(n+2), td:nth-child(n+2) {
        width: 23ch;
        max-width: 23ch;
    }
    </style>
""", unsafe_allow_html=True)



# MAIN
st.markdown("### 🔸 Канал: main")
main_rows = make_week_table("main", start_date, horizon)
main_df = pd.DataFrame([r[1] for r in main_rows], index=[r[0] for r in main_rows])
st.markdown(main_df.to_html(escape=False), unsafe_allow_html=True)

# ZODIAC
st.markdown("### 🔹 Канал: zodiac")
zodiac_rows = make_week_table("zodiac", start_date, horizon)
zodiac_df = pd.DataFrame([r[1] for r in zodiac_rows], index=[r[0] for r in zodiac_rows])
st.markdown(zodiac_df.to_html(escape=False), unsafe_allow_html=True)
